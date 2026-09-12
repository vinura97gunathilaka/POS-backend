from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.auth.audit import AuditBase

class BranchBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_id: Optional[int] = None
    logo_url: Optional[str] = None
    @field_validator('email', mode='before')
    @classmethod
    def empty_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return v


class BranchCreate(BranchBase):
    company_id: int

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_id: Optional[int] = None
    logo_url: Optional[str] = None
    status: Optional[str] = None
    logo_url: Optional[str] = None
    @field_validator('email', mode='before')
    @classmethod
    def empty_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return v


class BranchOut(BranchBase, AuditBase):
    company_id: int
