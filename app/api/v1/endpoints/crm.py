from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.crm import Customer, Supplier, LoyaltyRule, LoyaltyTransaction
from app.schemas.crm import (
    CustomerCreate, CustomerUpdate, CustomerOut,
    SupplierCreate, SupplierUpdate, SupplierOut,
    LoyaltyRuleCreate, LoyaltyRuleUpdate, LoyaltyRuleOut,
    LoyaltyTransactionOut
)
from app.schemas.response import APIResponse

router = APIRouter()

# --- Customers ---
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

    customer = Customer(**payload.dict(), created_by=current_user.id)
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

    for key, val in payload.dict(exclude_unset=True).items():
        setattr(customer, key, val)
    customer.updated_by = current_user.id
    db.commit()
    db.refresh(customer)
    return APIResponse(data=customer)

# --- Suppliers ---
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

    supplier = Supplier(**payload.dict(), created_by=current_user.id)
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

    for key, val in payload.dict(exclude_unset=True).items():
        setattr(supplier, key, val)
    supplier.updated_by = current_user.id
    db.commit()
    db.refresh(supplier)
    return APIResponse(data=supplier)

# --- Loyalty Rules & Transactions ---
@router.get("/loyalty/rules", response_model=APIResponse[List[LoyaltyRuleOut]])
def list_loyalty_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(LoyaltyRule).filter(LoyaltyRule.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(LoyaltyRule.company_id == current_user.company_id)
    rules = query.all()
    return APIResponse(data=rules)

@router.post("/loyalty/rules", response_model=APIResponse[LoyaltyRuleOut])
def create_loyalty_rule(
    payload: LoyaltyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    rule = LoyaltyRule(**payload.dict(), created_by=current_user.id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return APIResponse(data=rule)

@router.get("/loyalty/transactions/{customer_id}", response_model=APIResponse[List[LoyaltyTransactionOut]])
def list_loyalty_transactions(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not current_user.is_superadmin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    transactions = db.query(LoyaltyTransaction).filter(LoyaltyTransaction.customer_id == customer_id).all()
    return APIResponse(data=transactions)

