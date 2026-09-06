from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.security import get_password_hash
from app.models.rbac import User, Role, Permission, Branch, user_branches, UserRole, RolePermission
from app.schemas.rbac import (
    UserCreate, UserUpdate, UserOut,
    RoleCreate, RoleUpdate, RoleOut,
    PermissionCreate, PermissionOut
)
from app.schemas.response import APIResponse

router = APIRouter()

# --- Users ---
@router.get("/", response_model=APIResponse[List[UserOut]])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(User).filter(User.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(User.company_id == current_user.company_id)
    users = query.all()
    return APIResponse(data=users)

@router.post("/", response_model=APIResponse[UserOut])
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Cannot create user for another company")

    # Email uniqueness check
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    hashed_pw = get_password_hash(payload.password)
    user_dict = payload.dict(exclude={"password", "role_ids", "branch_ids"})
    user = User(**user_dict, hashed_password=hashed_pw, created_by=current_user.id)
    db.add(user)
    db.flush()

    # Assign Roles
    if payload.role_ids:
        for r_id in payload.role_ids:
            ur = UserRole(
                company_id=payload.company_id,
                user_id=user.id,
                role_id=r_id,
                created_by=current_user.id
            )
            db.add(ur)

    # Assign Branches
    if payload.branch_ids:
        branches = db.query(Branch).filter(Branch.id.in_(payload.branch_ids), Branch.company_id == payload.company_id).all()
        user.branches = branches

    db.commit()
    db.refresh(user)
    return APIResponse(data=user)

@router.put("/{id}", response_model=APIResponse[UserOut])
def update_user(
    id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_superadmin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user_data = payload.dict(exclude_unset=True, exclude={"password", "role_ids", "branch_ids"})
    for key, val in user_data.items():
        setattr(user, key, val)

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)

    # Re-assign Roles
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

    # Re-assign Branches
    if payload.branch_ids is not None:
        branches = db.query(Branch).filter(Branch.id.in_(payload.branch_ids), Branch.company_id == user.company_id).all()
        user.branches = branches

    user.updated_by = current_user.id
    db.commit()
    db.refresh(user)
    return APIResponse(data=user)

@router.delete("/{id}", response_model=APIResponse[str])
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_superadmin and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user.deleted_at = func.now()
    user.status = "archived"
    user.updated_by = current_user.id
    db.commit()
    return APIResponse(data="User deleted successfully.")

# --- Roles ---
@router.get("/roles", response_model=APIResponse[List[RoleOut]])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Role).filter(Role.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Role.company_id == current_user.company_id)
    roles = query.all()

    # Auto-seed standard roles if empty for this company
    if not roles:
        company_id = current_user.company_id
        # First ensure permissions are seeded
        perms = db.query(Permission).filter(Permission.company_id == company_id, Permission.deleted_at == None).all()
        if not perms:
            default_permissions = [
                {"name": "POS Billing & Checkout", "code": "pos:checkout", "description": "Access POS touch terminal and checkout billing"},
                {"name": "Read Catalog & Stock", "code": "inventory:read", "description": "View product catalog and branch stock levels"},
                {"name": "Adjust & Transfer Inventory", "code": "inventory:write", "description": "Perform stock adjustments and cross-branch transfers"},
                {"name": "Record GRN & Suppliers", "code": "procurement:grn", "description": "Manage vendor profiles and record Goods Received Notes"},
                {"name": "CRM & Loyalty Management", "code": "crm:manage", "description": "Enroll customers and manage loyalty points system"},
                {"name": "Users & Roles Settings", "code": "users:manage", "description": "View and manage store employees, roles and permissions"},
                {"name": "View Audit Trails", "code": "audit:read", "description": "Access system security audit logs viewer"},
                {"name": "Finance & Shift Control", "code": "finance:manage", "description": "Open and close shifts, view cash drawers and expenses"}
            ]
            for p in default_permissions:
                new_p = Permission(
                    company_id=company_id,
                    name=p["name"],
                    code=p["code"],
                    description=p["description"],
                    created_by=current_user.id
                )
                db.add(new_p)
            db.flush()
            perms = db.query(Permission).filter(Permission.company_id == company_id, Permission.deleted_at == None).all()

        perm_map = {p.code: p for p in perms}

        default_roles = [
            {
                "name": "Company Admin",
                "description": "Full access to all system functions, settings, and reports",
                "permissions": ["pos:checkout", "inventory:read", "inventory:write", "procurement:grn", "crm:manage", "users:manage", "audit:read", "finance:manage"]
            },
            {
                "name": "Branch Manager",
                "description": "Manages branch inventory, registers suppliers, and reviews shifts",
                "permissions": ["pos:checkout", "inventory:read", "inventory:write", "procurement:grn", "crm:manage", "audit:read", "finance:manage"]
            },
            {
                "name": "Cashier",
                "description": "Frontline sales checkout and CRM customer registration",
                "permissions": ["pos:checkout", "inventory:read", "crm:manage"]
            },
            {
                "name": "Stock Keeper",
                "description": "Manages products catalog, stock receipts and adjustments",
                "permissions": ["inventory:read", "inventory:write", "procurement:grn"]
            }
        ]

        for r in default_roles:
            role = Role(
                company_id=company_id,
                name=r["name"],
                description=r["description"],
                created_by=current_user.id
            )
            db.add(role)
            db.flush()
            for p_code in r["permissions"]:
                if p_code in perm_map:
                    rp = RolePermission(
                        company_id=company_id,
                        role_id=role.id,
                        permission_id=perm_map[p_code].id,
                        created_by=current_user.id
                    )
                    db.add(rp)
        db.commit()

        # Re-fetch roles
        query = db.query(Role).filter(Role.deleted_at == None)
        if not current_user.is_superadmin:
            query = query.filter(Role.company_id == company_id)
        roles = query.all()

    return APIResponse(data=roles)


@router.post("/roles", response_model=APIResponse[RoleOut])
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    role = Role(
        company_id=payload.company_id,
        name=payload.name,
        description=payload.description,
        created_by=current_user.id
    )
    db.add(role)
    db.flush()

    if payload.permission_ids:
        for p_id in payload.permission_ids:
            rp = RolePermission(
                company_id=payload.company_id,
                role_id=role.id,
                permission_id=p_id,
                created_by=current_user.id
            )
            db.add(rp)

    db.commit()
    db.refresh(role)
    return APIResponse(data=role)

@router.put("/roles/{id}", response_model=APIResponse[RoleOut])
def update_role(
    id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = db.query(Role).filter(Role.id == id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if not current_user.is_superadmin and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    role_data = payload.dict(exclude_unset=True, exclude={"permission_ids"})
    for key, val in role_data.items():
        setattr(role, key, val)

    if payload.permission_ids is not None:
        db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
        for p_id in payload.permission_ids:
            rp = RolePermission(
                company_id=role.company_id,
                role_id=role.id,
                permission_id=p_id,
                created_by=current_user.id
            )
            db.add(rp)

    role.updated_by = current_user.id
    db.commit()
    db.refresh(role)
    return APIResponse(data=role)

# --- Permissions ---
@router.get("/permissions", response_model=APIResponse[List[PermissionOut]])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Permission).filter(Permission.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Permission.company_id == current_user.company_id)
    permissions = query.all()

    # Auto-seed if empty for this company
    if not permissions:
        company_id = current_user.company_id
        default_permissions = [
            {"name": "POS Billing & Checkout", "code": "pos:checkout", "description": "Access POS touch terminal and checkout billing"},
            {"name": "Read Catalog & Stock", "code": "inventory:read", "description": "View product catalog and branch stock levels"},
            {"name": "Adjust & Transfer Inventory", "code": "inventory:write", "description": "Perform stock adjustments and cross-branch transfers"},
            {"name": "Record GRN & Suppliers", "code": "procurement:grn", "description": "Manage vendor profiles and record Goods Received Notes"},
            {"name": "CRM & Loyalty Management", "code": "crm:manage", "description": "Enroll customers and manage loyalty points system"},
            {"name": "Users & Roles Settings", "code": "users:manage", "description": "View and manage store employees, roles and permissions"},
            {"name": "View Audit Trails", "code": "audit:read", "description": "Access system security audit logs viewer"},
            {"name": "Finance & Shift Control", "code": "finance:manage", "description": "Open and close shifts, view cash drawers and expenses"}
        ]
        for p in default_permissions:
            new_p = Permission(
                company_id=company_id,
                name=p["name"],
                code=p["code"],
                description=p["description"],
                created_by=current_user.id
            )
            db.add(new_p)
        db.commit()

        # Re-fetch permissions
        query = db.query(Permission).filter(Permission.deleted_at == None)
        if not current_user.is_superadmin:
            query = query.filter(Permission.company_id == company_id)
        permissions = query.all()

    return APIResponse(data=permissions)

@router.post("/permissions", response_model=APIResponse[PermissionOut])
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    permission = Permission(**payload.dict(), created_by=current_user.id)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return APIResponse(data=permission)
