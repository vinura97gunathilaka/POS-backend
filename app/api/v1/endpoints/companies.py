from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.api.deps import get_current_user, get_current_superadmin
from app.models.auth import User, Role
from app.models.organization import Company
from app.schemas.organization import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanyOut, 
    CompanyOnboard, 
    SubscriptionUpdate
)
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse[List[CompanyOut]])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    companies = db.query(Company).filter(Company.deleted_at == None).all()
    return APIResponse(data=companies, message="Companies retrieved successfully")

@router.post("/", response_model=APIResponse[CompanyOut])
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    company = Company(**payload.dict(), created_by=current_user.id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return APIResponse(data=company, message="Company created successfully")

from app.models.auth import User, Role, UserRole
from app.models.organization import Company, Branch
from app.api.v1.endpoints.users import seed_company_permissions_and_roles

@router.post("/onboard", response_model=APIResponse[CompanyOut])
def onboard_company(
    payload: CompanyOnboard,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    # Check if admin email already exists
    existing_user = db.query(User).filter(User.email == payload.admin_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email {payload.admin_email} already exists."
        )
    
    # 1. Create Tenant Company
    company = Company(
        name=payload.company_name,
        phone=payload.phone,
        subscription_plan=payload.subscription_plan or "pro",
        max_users=payload.max_users,
        max_branches=payload.max_branches,
        status="active",
        created_by=current_user.id
    )
    db.add(company)
    db.flush() # get company.id

    # 2. Create Primary Branch for the Company
    primary_branch = Branch(
        company_id=company.id,
        name=payload.primary_branch_name or "Main Branch",
        phone=payload.phone,
        created_by=current_user.id
    )
    db.add(primary_branch)
    db.flush()

    # 3. Create Primary Company Admin User & Register under Primary Branch
    hashed_pwd = get_password_hash(payload.admin_password)
    admin_user = User(
        company_id=company.id,
        employee_id=f"EMP-{company.id}-0001",
        name=payload.admin_name,
        email=payload.admin_email,
        phone=payload.phone,
        hashed_password=hashed_pwd,
        is_superadmin=False,
        has_system_access=True,
        must_change_password=False,
        created_by=current_user.id
    )
    admin_user.branches = [primary_branch]
    db.add(admin_user)
    db.flush()

    # 4. Seed default company roles & permissions and assign 'Company Admin' role
    seed_company_permissions_and_roles(db, company.id, admin_user.id)
    admin_role = db.query(Role).filter(Role.company_id == company.id, Role.name == "Company Admin").first()
    if admin_role:
        ur = UserRole(
            company_id=company.id,
            user_id=admin_user.id,
            role_id=admin_role.id,
            created_by=current_user.id
        )
        db.add(ur)

    db.commit()
    db.refresh(company)
    
    return APIResponse(
        data=company, 
        message=f"Company '{company.name}' and Primary Admin account '{admin_user.email}' onboarded successfully"
    )

@router.get("/{id}", response_model=APIResponse[CompanyOut])
def get_company(
    id: int,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this company's profile"
        )
    company = db.query(Company).filter(Company.id == id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return APIResponse(data=company, message="Company details retrieved successfully")

@router.put("/{id}", response_model=APIResponse[CompanyOut])
def update_company(
    id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators or your own company admin can update this company"
        )
    company = db.query(Company).filter(Company.id == id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    for key, val in payload.dict(exclude_unset=True).items():
        setattr(company, key, val)
    company.updated_by = current_user.id
    db.commit()
    db.refresh(company)
    return APIResponse(data=company, message="Company profile updated successfully")

@router.patch("/{id}/subscription", response_model=APIResponse[CompanyOut])
def update_company_subscription(
    id: int,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    company = db.query(Company).filter(Company.id == id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for key, val in payload.dict(exclude_unset=True).items():
        setattr(company, key, val)
    company.updated_by = current_user.id
    db.commit()
    db.refresh(company)
    return APIResponse(
        data=company, 
        message=f"Subscription for '{company.name}' updated successfully (Status: {company.status}, Plan: {company.subscription_plan})"
    )

