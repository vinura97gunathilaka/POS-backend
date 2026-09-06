from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from app.api.deps import get_current_user
from app.models.rbac import User, Company, Branch
from app.schemas.auth import Token, ForgotPasswordPayload, ResetPasswordPayload
from app.schemas.rbac import UserOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.post("/login", response_model=APIResponse[Token])
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Retrieve user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return APIResponse(
        data=Token(access_token=access_token, refresh_token=refresh_token)
    )

@router.post("/refresh", response_model=APIResponse[Token])
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    from jose import jwt, JWTError
    from app.core.config import settings
    from app.core.security import ALGORITHM

    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive or not found",
        )

    new_access = create_access_token(subject=user.id)
    new_refresh = create_refresh_token(subject=user.id)
    return APIResponse(
        data=Token(access_token=new_access, refresh_token=new_refresh)
    )

@router.get("/me", response_model=APIResponse[UserOut])
def get_me(response: Response, current_user: User = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return APIResponse(data=current_user)

@router.post("/forgot-password", response_model=APIResponse[str])
def forgot_password(payload: ForgotPasswordPayload, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Avoid user enumeration attacks, return success but don't do anything
        return APIResponse(data="Password reset link sent to registered email if exists.")
    
    # In a real app, send email with a secure token.
    # Here we mock it.
    return APIResponse(data="Password reset link sent to registered email if exists.")

@router.post("/reset-password", response_model=APIResponse[str])
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    # Validate token and reset password. Mocked here.
    return APIResponse(data="Password has been reset successfully.")

# Setup initial admin route to help testing
@router.post("/setup-initial-admin", response_model=APIResponse[dict])
def setup_initial_admin(db: Session = Depends(get_db)):
    # Check if any user exists
    user_exists = db.query(User).first()
    if user_exists:
        return APIResponse(success=False, error="Setup already completed. User database is not empty.")
    
    # Create company
    company = Company(
        name="Smart POS Corp",
        logo_url="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d",
        phone="+94112222222",
        email="info@smartpos.com",
        address="100 Galle Road, Colombo",
        settings={}
    )
    db.add(company)
    db.flush()

    # Create branch
    branch = Branch(
        company_id=company.id,
        name="Head Office Branch",
        address="100 Galle Road, Colombo",
        phone="+94112222222",
        email="headoffice@smartpos.com"
    )
    db.add(branch)
    db.flush()

    # Create user
    user = User(
        company_id=company.id,
        name="Super Administrator",
        email="admin@smartpos.com",
        hashed_password=get_password_hash("admin123"),
        phone="+94777123456",
        is_superadmin=True,
        status="active"
    )
    db.add(user)
    db.flush()

    # Connect user to branch
    user.branches.append(branch)

    # Operational defaults setup
    from app.models.finance import CashDrawer, BankAccount
    from app.models.crm import LoyaltyRule

    drawer = CashDrawer(
        company_id=company.id,
        branch_id=branch.id,
        name="Default Cash Drawer",
        balance=0.00,
        status="active"
    )
    db.add(drawer)

    bank = BankAccount(
        company_id=company.id,
        branch_id=branch.id,
        bank_name="Default Bank",
        account_number="1234567890",
        balance=0.00,
        status="active"
    )
    db.add(bank)

    rule = LoyaltyRule(
        company_id=company.id,
        name="Default Loyalty Rule",
        spend_amount=100.00,
        points_earned=1,
        point_value=1.00,
        status="active"
    )
    db.add(rule)

    db.commit()


    return APIResponse(
        data={
            "message": "Initial seed complete. Use email admin@smartpos.com and password admin123 to log in.",
            "company_id": company.id,
            "branch_id": branch.id,
            "user_id": user.id
        }
    )
