from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from app.schemas.auth.audit import AuditBase

class CompanyBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    settings: Dict[str, Any] = {}

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class CompanyOut(CompanyBase, AuditBase):
    pass
