from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User, Role, RolePermission
from app.schemas.auth import (
    RoleCreate,
    RoleUpdate,
    RoleOut,
    RolePermissionAssign,
)
from app.schemas.response import APIResponse
from app.api.v1.endpoints.users.permissions import seed_company_permissions_and_roles

router = APIRouter()

# ============================================================================
#  ROLES CRUD ENDPOINTS
# ============================================================================

@router.get("/roles", response_model=APIResponse[List[RoleOut]])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.company_id:
        seed_company_permissions_and_roles(db, current_user.company_id, current_user.id)
    query = db.query(Role).filter(Role.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Role.company_id == current_user.company_id)
    roles = query.all()
    return APIResponse(data=roles, message="Roles retrieved successfully")

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
    return APIResponse(data=role, message=f"Role '{role.name}' created successfully")

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
    return APIResponse(data=role, message=f"Role '{role.name}' updated successfully")

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
    return APIResponse(data="Role deleted successfully", message=f"Role '{role.name}' deleted successfully")

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
    return APIResponse(data=role, message=f"Permissions for role '{role.name}' updated successfully")
