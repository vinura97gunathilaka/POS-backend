from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, EmailStr
from app.schemas.auth import AuditBase

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
