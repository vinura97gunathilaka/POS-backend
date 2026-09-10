from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.api.deps import get_current_user, require_permission
from app.models.auth import User, Role, Permission, UserRole, RolePermission
from app.models.organization import Branch
from app.schemas.auth import (
    UserCreate, UserUpdate, UserOut,
    RoleCreate, RoleUpdate, RoleOut, RolePermissionAssign, UserRoleAssign,
    PermissionCreate, PermissionUpdate, PermissionOut
)
from app.schemas.response import APIResponse

router = APIRouter()

SYSTEM_PERMISSIONS = [
    {"name": "Create User", "code": "CREATE_USER", "description": "Create new store employees and system users"},
    {"name": "View Users", "code": "VIEW_USER", "description": "View list of store employees and profiles"},
    {"name": "Update User", "code": "UPDATE_USER", "description": "Modify user information and status"},
    {"name": "Delete User", "code": "DELETE_USER", "description": "Deactivate or remove store users"},

    {"name": "Create Role", "code": "CREATE_ROLE", "description": "Create custom roles for the company"},
    {"name": "View Roles", "code": "VIEW_ROLE", "description": "View active roles and assigned permissions"},
    {"name": "Update Role", "code": "UPDATE_ROLE", "description": "Modify role names and descriptions"},
    {"name": "Delete Role", "code": "DELETE_ROLE", "description": "Remove custom company roles"},
    {"name": "Assign Permissions", "code": "ASSIGN_PERMISSIONS", "description": "Assign or revoke permissions from roles"},

    {"name": "Create Order", "code": "CREATE_ORDER", "description": "Create new dine-in, takeaway or delivery orders"},
    {"name": "View Orders", "code": "VIEW_ORDER", "description": "View active and historic customer orders"},
    {"name": "Checkout Order", "code": "CHECKOUT_ORDER", "description": "Process payments and print receipts"},
    {"name": "Hold Order", "code": "HOLD_ORDER", "description": "Park or recall held bills"},
    {"name": "Cancel / Void Order", "code": "CANCEL_ORDER", "description": "Void or refund completed/active sales"},

    {"name": "View Kitchen Stream", "code": "VIEW_KITCHEN", "description": "Access Kitchen Display System (KDS)"},
    {"name": "Update KDS Ticket Status", "code": "UPDATE_KITCHEN_STATUS", "description": "Mark tickets as preparing, ready, or served"},

    {"name": "View Inventory", "code": "VIEW_INVENTORY", "description": "View product stock levels and transaction logs"},
    {"name": "Manage Stock Adjustments", "code": "MANAGE_INVENTORY", "description": "Perform stock adjustments, wastage logs and branch transfers"},
    {"name": "View Recipes", "code": "VIEW_RECIPE", "description": "View item Bill of Materials and recipe costing"},
    {"name": "Manage Recipes", "code": "MANAGE_RECIPE", "description": "Create and update recipe ingredient formulas"},

    {"name": "View Procurement", "code": "VIEW_PROCUREMENT", "description": "View purchase orders and goods received notes"},
    {"name": "Receive GRN", "code": "CREATE_GRN", "description": "Record incoming shipments and update stock/cost"},
    {"name": "Manage Suppliers", "code": "MANAGE_SUPPLIER", "description": "Manage vendor details and supplier ledgers"},

    {"name": "View Business Reports", "code": "VIEW_REPORTS", "description": "View sales, inventory, and financial summaries"},
    {"name": "Export Data", "code": "EXPORT_REPORTS", "description": "Export reports in PDF and CSV format"},
    {"name": "Manage Shifts & Expenses", "code": "MANAGE_FINANCE", "description": "Open/close cash drawer shifts and log expenses"},
    {"name": "View Audit History", "code": "VIEW_AUDIT_LOGS", "description": "View system audit logs and action history"}
]

STANDARD_ROLES = [
    {
        "name": "Company Admin",
        "description": "Full administrative control for all company operations, branches, and staff",
        "permissions": ["CREATE_USER", "VIEW_USER", "UPDATE_USER", "DELETE_USER", "CREATE_ROLE", "VIEW_ROLE", "UPDATE_ROLE", "DELETE_ROLE", "ASSIGN_PERMISSIONS", "CREATE_ORDER", "VIEW_ORDER", "CHECKOUT_ORDER", "HOLD_ORDER", "CANCEL_ORDER", "VIEW_KITCHEN", "UPDATE_KITCHEN_STATUS", "VIEW_INVENTORY", "MANAGE_INVENTORY", "VIEW_RECIPE", "MANAGE_RECIPE", "VIEW_PROCUREMENT", "CREATE_GRN", "MANAGE_SUPPLIER", "VIEW_REPORTS", "EXPORT_REPORTS", "MANAGE_FINANCE", "VIEW_AUDIT_LOGS"]
    },
    {
        "name": "Branch Manager",
        "description": "Manages branch staff, inventory, shifts, procurement, and daily order operations",
        "permissions": ["CREATE_USER", "VIEW_USER", "UPDATE_USER", "CREATE_ORDER", "VIEW_ORDER", "CHECKOUT_ORDER", "HOLD_ORDER", "CANCEL_ORDER", "VIEW_KITCHEN", "UPDATE_KITCHEN_STATUS", "VIEW_INVENTORY", "MANAGE_INVENTORY", "VIEW_RECIPE", "MANAGE_RECIPE", "VIEW_PROCUREMENT", "CREATE_GRN", "MANAGE_SUPPLIER", "VIEW_REPORTS", "EXPORT_REPORTS", "MANAGE_FINANCE", "VIEW_AUDIT_LOGS"]
    },
    {
        "name": "Cashier",
        "description": "Frontline POS checkout operator handling billing, cash drawer, and hold/recall bills",
        "permissions": ["CREATE_ORDER", "VIEW_ORDER", "CHECKOUT_ORDER", "HOLD_ORDER", "VIEW_INVENTORY", "MANAGE_SUPPLIER"]
    },
    {
        "name": "Chef / Kitchen Staff",
        "description": "Kitchen Display System operator preparing orders and managing KOT ticket statuses",
        "permissions": ["VIEW_KITCHEN", "UPDATE_KITCHEN_STATUS", "VIEW_ORDER", "VIEW_RECIPE"]
    },
    {
        "name": "Waiter / Floor Staff",
        "description": "Floor service staff taking customer orders, assigning tables, and sending KOTs",
        "permissions": ["CREATE_ORDER", "VIEW_ORDER", "HOLD_ORDER", "VIEW_KITCHEN"]
    }
]

def seed_company_permissions_and_roles(db: Session, company_id: int, user_id: int):
    existing_perms = db.query(Permission).filter(Permission.company_id == company_id, Permission.deleted_at == None).all()
    perm_map = {p.code: p for p in existing_perms}

    for p in SYSTEM_PERMISSIONS:
        if p["code"] not in perm_map:
            new_p = Permission(
                company_id=company_id,
                name=p["name"],
                code=p["code"],
                description=p["description"],
                created_by=user_id
            )
            db.add(new_p)
            db.flush()
            perm_map[p["code"]] = new_p

    existing_roles = db.query(Role).filter(Role.company_id == company_id, Role.deleted_at == None).all()
    role_map = {r.name: r for r in existing_roles}

    for r in STANDARD_ROLES:
        if r["name"] not in role_map:
            role = Role(
                company_id=company_id,
                name=r["name"],
                description=r["description"],
                created_by=user_id
            )
            db.add(role)
            db.flush()
            role_map[r["name"]] = role
            for p_code in r["permissions"]:
                if p_code in perm_map:
                    rp = RolePermission(
                        company_id=company_id,
                        role_id=role.id,
                        permission_id=perm_map[p_code].id,
                        created_by=user_id
                    )
                    db.add(rp)

    db.commit()

# ============================================================================
#  1. ROLES CRUD ENDPOINTS (Must be defined before /{id} generic user route)
# ============================================================================

@router.get("/roles", response_model=APIResponse[List[RoleOut]])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    seed_company_permissions_and_roles(db, current_user.company_id, current_user.id)
    query = db.query(Role).filter(Role.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Role.company_id == current_user.company_id)
    roles = query.all()
    return APIResponse(data=roles)

@router.get("/roles/{id}", response_model=APIResponse[RoleOut])
def get_role_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = db.query(Role).filter(Role.id == id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if not current_user.is_superadmin and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return APIResponse(data=role)

@router.post("/roles", response_model=APIResponse[RoleOut])
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_ROLE"))
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
    current_user: User = Depends(require_permission("UPDATE_ROLE"))
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

@router.delete("/roles/{id}", response_model=APIResponse[str])
def delete_role(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("DELETE_ROLE"))
):
    role = db.query(Role).filter(Role.id == id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if not current_user.is_superadmin and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    role.deleted_at = datetime.utcnow()
    role.status = "deleted"
    role.updated_by = current_user.id
    db.commit()
    return APIResponse(data="Role deleted successfully")

@router.post("/roles/{role_id}/permissions", response_model=APIResponse[RoleOut])
def assign_role_permissions(
    role_id: int,
    payload: RolePermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ASSIGN_PERMISSIONS"))
):
    role = db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if not current_user.is_superadmin and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    for p_id in payload.permission_ids:
        rp = RolePermission(
            company_id=role.company_id,
            role_id=role.id,
            permission_id=p_id,
            created_by=current_user.id
        )
        db.add(rp)

    db.commit()
    db.refresh(role)
    return APIResponse(data=role)

# ============================================================================
#  2. PERMISSIONS CRUD ENDPOINTS (Must be defined before /{id} generic user route)
# ============================================================================

@router.get("/permissions", response_model=APIResponse[List[PermissionOut]])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    seed_company_permissions_and_roles(db, current_user.company_id, current_user.id)
    query = db.query(Permission).filter(Permission.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Permission.company_id == current_user.company_id)
    permissions = query.all()
    return APIResponse(data=permissions)

@router.get("/permissions/{id}", response_model=APIResponse[PermissionOut])
def get_permission_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    permission = db.query(Permission).filter(Permission.id == id, Permission.deleted_at == None).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    if not current_user.is_superadmin and permission.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return APIResponse(data=permission)

@router.post("/permissions", response_model=APIResponse[PermissionOut])
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ASSIGN_PERMISSIONS"))
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    permission = Permission(**payload.dict(), created_by=current_user.id)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return APIResponse(data=permission)

@router.put("/permissions/{id}", response_model=APIResponse[PermissionOut])
def update_permission(
    id: int,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ASSIGN_PERMISSIONS"))
):
    permission = db.query(Permission).filter(Permission.id == id, Permission.deleted_at == None).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    if not current_user.is_superadmin and permission.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    data = payload.dict(exclude_unset=True)
    for key, val in data.items():
        setattr(permission, key, val)

    permission.updated_by = current_user.id
    db.commit()
    db.refresh(permission)
    return APIResponse(data=permission)

@router.delete("/permissions/{id}", response_model=APIResponse[str])
def delete_permission(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ASSIGN_PERMISSIONS"))
):
    permission = db.query(Permission).filter(Permission.id == id, Permission.deleted_at == None).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    if not current_user.is_superadmin and permission.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    permission.deleted_at = datetime.utcnow()
    permission.status = "deleted"
    permission.updated_by = current_user.id
    db.commit()
    return APIResponse(data="Permission deleted successfully")

# ============================================================================
#  3. USERS CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=APIResponse[List[UserOut]])
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

@router.post("", response_model=APIResponse[UserOut])
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_USER"))
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        company_id=payload.company_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=get_password_hash(payload.password),
        is_superadmin=payload.is_superadmin if current_user.is_superadmin else False,
        status="active",
        created_by=current_user.id
    )
    db.add(user)
    db.flush()

    if payload.role_ids:
        for r_id in payload.role_ids:
            ur = UserRole(
                company_id=payload.company_id,
                user_id=user.id,
                role_id=r_id,
                created_by=current_user.id
            )
            db.add(ur)

    if payload.branch_ids:
        branches = db.query(Branch).filter(Branch.id.in_(payload.branch_ids)).all()
        user.branches = branches

    db.commit()
    db.refresh(user)
    return APIResponse(data=user)

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

