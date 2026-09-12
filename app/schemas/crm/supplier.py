from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, EmailStr
from app.schemas.auth import AuditBase

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
