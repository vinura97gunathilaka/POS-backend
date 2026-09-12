from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.crm.customer import Customer
from app.schemas.crm.customer import CustomerCreate, CustomerUpdate, CustomerOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/customers", response_model=APIResponse[List[CustomerOut]])
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Customer).filter(Customer.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Customer.company_id == current_user.company_id)
    customers = query.all()
    return APIResponse(data=customers)

@router.post("/customers", response_model=APIResponse[CustomerOut])
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    customer = Customer(**payload.model_dump(), created_by=current_user.id)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return APIResponse(data=customer)

@router.put("/customers/{id}", response_model=APIResponse[CustomerOut])
def update_customer(
    id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == id, Customer.deleted_at == None).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not current_user.is_superadmin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, val)
    customer.updated_by = current_user.id
    db.commit()
    db.refresh(customer)
    return APIResponse(data=customer)
