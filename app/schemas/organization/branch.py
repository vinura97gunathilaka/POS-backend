from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.auth.audit import AuditBase

class BranchBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_id: Optional[int] = None

class BranchCreate(BranchBase):
    company_id: int

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_id: Optional[int] = None
    status: Optional[str] = None

class BranchOut(BranchBase, AuditBase):
    company_id: int
