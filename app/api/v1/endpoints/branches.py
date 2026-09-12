from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.models.organization import Branch, Company
from app.schemas.organization import BranchCreate, BranchUpdate, BranchOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse[List[BranchOut]])
def list_branches(
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Branch).filter(Branch.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Branch.company_id == current_user.company_id)
    elif company_id:
        query = query.filter(Branch.company_id == company_id)
    branches = query.all()
    return APIResponse(data=branches, message="Branches retrieved successfully")

@router.post("/", response_model=APIResponse[BranchOut])
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_BRANCH"))
):
    target_company_id = payload.company_id if current_user.is_superadmin else current_user.company_id
    if not current_user.is_superadmin and payload.company_id and current_user.company_id != payload.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create branches for another company"
        )
    
    if target_company_id:
        company = db.query(Company).filter(Company.id == target_company_id).first()
        if company and company.max_branches:
            current_branch_count = db.query(Branch).filter(Branch.company_id == target_company_id, Branch.deleted_at == None).count()
            if current_branch_count >= company.max_branches:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Company branch limit reached ({company.max_branches} branches max on '{company.subscription_plan}' plan). Upgrade plan to create more branches."
                )

    data = payload.dict()
    data["company_id"] = target_company_id
    branch = Branch(**data, created_by=current_user.id)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return APIResponse(data=branch, message=f"Branch '{branch.name}' created successfully")

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
    current_user: User = Depends(require_permission("UPDATE_BRANCH"))
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
    return APIResponse(data=branch, message=f"Branch '{branch.name}' updated successfully")

@router.delete("/{id}", response_model=APIResponse[str])
def delete_branch(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("DELETE_BRANCH"))
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
    return APIResponse(data="Branch deactivated successfully.", message=f"Branch '{branch.name}' deactivated successfully")
