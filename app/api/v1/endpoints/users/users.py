from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.api.deps import require_permission
from app.models.auth import User, UserRole
from app.models.organization import Branch, Company
from app.schemas.auth import (
    UserCreate,
    UserUpdate,
    UserOut,
    UserRoleAssign,
)
from app.schemas.response import APIResponse

router = APIRouter()

# ============================================================================
#  USERS CRUD ENDPOINTS
# ============================================================================

@router.get("/", response_model=APIResponse[List[UserOut]])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_USER"))
):
    query = db.query(User).filter(User.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(User.company_id == current_user.company_id)
    users = query.all()
    return APIResponse(data=users)

@router.get("/{id}", response_model=APIResponse[UserOut])
def get_user_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_USER"))
):
    user = db.query(User).filter(User.id == id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_superadmin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return APIResponse(data=user)

def generate_next_employee_id(db: Session, company_id: Optional[int]) -> str:
    prefix = f"EMP-{(company_id or 0)}"
    count = db.query(User).filter(User.company_id == company_id).count() + 1
    candidate = f"{prefix}-{count:04d}"
    while db.query(User).filter(User.employee_id == candidate).first():
        count += 1
        candidate = f"{prefix}-{count:04d}"
    return candidate

@router.post("/", response_model=APIResponse[UserOut])
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_USER"))
):
    target_company_id = payload.company_id if current_user.is_superadmin else current_user.company_id
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if target_company_id:
        company = db.query(Company).filter(Company.id == target_company_id).first()
        if company and company.max_users:
            current_user_count = db.query(User).filter(User.company_id == target_company_id, User.deleted_at == None).count()
            if current_user_count >= company.max_users:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Company user limit reached ({company.max_users} users max on '{company.subscription_plan}' plan). Upgrade plan to create more users."
                )

    # 1. Auto-generate or format Employee ID
    emp_id = payload.employee_id.strip() if payload.employee_id else generate_next_employee_id(db, target_company_id)
    existing_emp = db.query(User).filter(User.employee_id == emp_id, User.company_id == target_company_id, User.deleted_at == None).first()
    if existing_emp:
        raise HTTPException(status_code=400, detail=f"Employee ID '{emp_id}' is already assigned in this company.")

    # 2. Unique NIC check
    if payload.nic:
        existing_nic = db.query(User).filter(User.nic == payload.nic, User.company_id == target_company_id, User.deleted_at == None).first()
        if existing_nic:
            raise HTTPException(status_code=400, detail=f"NIC '{payload.nic}' is already registered to another employee in this company.")

    # 3. Unique Email check if provided
    if payload.email:
        existing_email = db.query(User).filter(User.email == payload.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail=f"Email '{payload.email}' is already registered.")

    # 4. System access and password logic
    has_access = payload.has_system_access
    raw_password = payload.password if payload.password else f"Pass#{emp_id}"
    hashed_pwd = get_password_hash(raw_password)

    user = User(
        company_id=target_company_id,
        employee_id=emp_id,
        nic=payload.nic,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        hashed_password=hashed_pwd,
        is_superadmin=payload.is_superadmin if current_user.is_superadmin else False,
        has_system_access=has_access,
        must_change_password=True if has_access else False,
        status="active",
        created_by=current_user.id
    )
    db.add(user)
    db.flush()

    if payload.role_ids:
        for r_id in payload.role_ids:
            ur = UserRole(
                company_id=target_company_id,
                user_id=user.id,
                role_id=r_id,
                created_by=current_user.id
            )
            db.add(ur)

    if payload.branch_ids:
        branches = db.query(Branch).filter(Branch.id.in_(payload.branch_ids), Branch.company_id == target_company_id, Branch.deleted_at == None).all()
        if len(branches) != len(payload.branch_ids):
            raise HTTPException(status_code=400, detail="One or more specified branch IDs do not belong to this company.")
        user.branches = branches
    elif target_company_id:
        primary_branch = db.query(Branch).filter(Branch.company_id == target_company_id, Branch.deleted_at == None).first()
        if primary_branch:
            user.branches = [primary_branch]

    db.commit()
    db.refresh(user)
    
    msg_suffix = f" (Default password: '{raw_password}')" if has_access and not payload.password else ""
    return APIResponse(
        data=user, 
        message=f"Employee '{user.name}' ({user.employee_id}) created successfully.{msg_suffix}"
    )

@router.put("/{id}", response_model=APIResponse[UserOut])
def update_user(
    id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("UPDATE_USER"))
):
    user = db.query(User).filter(User.id == id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_superadmin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    data = payload.dict(exclude_unset=True, exclude={"password", "role_ids", "branch_ids"})
    for key, val in data.items():
        setattr(user, key, val)

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)

    if payload.role_ids is not None:
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for r_id in payload.role_ids:
            ur = UserRole(
                company_id=user.company_id,
                user_id=user.id,
                role_id=r_id,
                created_by=current_user.id
            )
            db.add(ur)

    if payload.branch_ids is not None:
        branches = db.query(Branch).filter(Branch.id.in_(payload.branch_ids)).all()
        user.branches = branches

    user.updated_by = current_user.id
    db.commit()
    db.refresh(user)
    return APIResponse(data=user)

@router.delete("/{id}", response_model=APIResponse[str])
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("DELETE_USER"))
):
    user = db.query(User).filter(User.id == id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_superadmin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own user account")

    user.deleted_at = datetime.utcnow()
    user.status = "deleted"
    user.updated_by = current_user.id
    db.commit()
    return APIResponse(data="User deleted successfully")

@router.post("/{user_id}/roles", response_model=APIResponse[UserOut])
def assign_user_roles(
    user_id: int,
    payload: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ASSIGN_PERMISSIONS"))
):
    user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_superadmin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.query(UserRole).filter(UserRole.user_id == user.id).delete()
    for r_id in payload.role_ids:
        ur = UserRole(
            company_id=user.company_id,
            user_id=user.id,
            role_id=r_id,
            created_by=current_user.id
        )
        db.add(ur)

    db.commit()
    db.refresh(user)
    return APIResponse(data=user)
