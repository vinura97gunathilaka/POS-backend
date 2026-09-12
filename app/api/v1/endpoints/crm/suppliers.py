from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.crm.supplier import Supplier
from app.schemas.crm.supplier import SupplierCreate, SupplierUpdate, SupplierOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/suppliers", response_model=APIResponse[List[SupplierOut]])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Supplier).filter(Supplier.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Supplier.company_id == current_user.company_id)
    suppliers = query.all()
    return APIResponse(data=suppliers)

@router.post("/suppliers", response_model=APIResponse[SupplierOut])
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    supplier = Supplier(**payload.model_dump(), created_by=current_user.id)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return APIResponse(data=supplier)

@router.put("/suppliers/{id}", response_model=APIResponse[SupplierOut])
def update_supplier(
    id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    supplier = db.query(Supplier).filter(Supplier.id == id, Supplier.deleted_at == None).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not current_user.is_superadmin and supplier.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, key, val)
    supplier.updated_by = current_user.id
    db.commit()
    db.refresh(supplier)
    return APIResponse(data=supplier)
