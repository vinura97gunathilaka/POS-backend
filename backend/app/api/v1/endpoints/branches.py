from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.rbac import Branch, User
from app.schemas.rbac import BranchCreate, BranchUpdate, BranchOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse[List[BranchOut]])
def list_branches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Branch).filter(Branch.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Branch.company_id == current_user.company_id)
    branches = query.all()
    return APIResponse(data=branches)

@router.post("/", response_model=APIResponse[BranchOut])
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create branches for another company"
        )
    branch = Branch(**payload.dict(), created_by=current_user.id)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return APIResponse(data=branch)

@router.get("/{id}", response_model=APIResponse[BranchOut])
def get_branch(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    branch = db.query(Branch).filter(Branch.id == id, Branch.deleted_at == None).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if not current_user.is_superadmin and branch.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return APIResponse(data=branch)

@router.put("/{id}", response_model=APIResponse[BranchOut])
def update_branch(
    id: int,
    payload: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    branch = db.query(Branch).filter(Branch.id == id, Branch.deleted_at == None).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if not current_user.is_superadmin and branch.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    for key, val in payload.dict(exclude_unset=True).items():
        setattr(branch, key, val)
    branch.updated_by = current_user.id
    db.commit()
    db.refresh(branch)
    return APIResponse(data=branch)

@router.delete("/{id}", response_model=APIResponse[str])
def delete_branch(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    branch = db.query(Branch).filter(Branch.id == id, Branch.deleted_at == None).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if not current_user.is_superadmin and branch.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    branch.deleted_at = func.now()
    branch.status = "archived"
    branch.updated_by = current_user.id
    db.commit()
    return APIResponse(data="Branch deactivated successfully.")
