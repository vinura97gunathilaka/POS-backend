from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, EmailStr
from app.schemas.auth import AuditBase

# --- Customer ---
class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Decimal = Decimal("0.00")
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    company_id: int

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class CustomerOut(CustomerBase, AuditBase):
    company_id: int
    balance: Decimal
    points: int

# --- Supplier ---
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    company_id: int

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

class SupplierOut(SupplierBase, AuditBase):
    company_id: int
    ledger_balance: Decimal

# --- Loyalty Rule ---
class LoyaltyRuleBase(BaseModel):
    name: str
    spend_amount: Decimal = Decimal("100.00")
    points_earned: int = 1
    point_value: Decimal = Decimal("1.00")

class LoyaltyRuleCreate(LoyaltyRuleBase):
    company_id: int

class LoyaltyRuleUpdate(BaseModel):
    name: Optional[str] = None
    spend_amount: Optional[Decimal] = None
    points_earned: Optional[int] = None
    point_value: Optional[Decimal] = None
    status: Optional[str] = None

class LoyaltyRuleOut(LoyaltyRuleBase, AuditBase):
    company_id: int

# --- Loyalty Transaction ---
class LoyaltyTransactionBase(BaseModel):
    points: int
    type: str # earn, redeem, adjust, expire
    reference_id: Optional[str] = None
    description: Optional[str] = None

class LoyaltyTransactionOut(LoyaltyTransactionBase, AuditBase):
    company_id: int
    customer_id: int

