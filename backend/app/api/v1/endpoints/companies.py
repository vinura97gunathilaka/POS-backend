from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.rbac import Company, User
from app.schemas.rbac import CompanyCreate, CompanyUpdate, CompanyOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse[List[CompanyOut]])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can list all companies"
        )
    companies = db.query(Company).filter(Company.deleted_at == None).all()
    return APIResponse(data=companies)

@router.post("/", response_model=APIResponse[CompanyOut])
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create companies"
        )
    company = Company(**payload.dict(), created_by=current_user.id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return APIResponse(data=company)

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
    return APIResponse(data=company)

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
    return APIResponse(data=company)
