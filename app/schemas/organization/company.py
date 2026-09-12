from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.auth.audit import AuditBase

class CompanyBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    status: str = "active"
    subscription_plan: str = "pro"
    subscription_expires_at: Optional[datetime] = None
    max_users: Optional[int] = None
    max_branches: Optional[int] = None
    settings: Dict[str, Any] = {}
    @field_validator('email', mode='before')
    @classmethod
    def empty_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return v


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
    subscription_plan: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None
    max_users: Optional[int] = None
    max_branches: Optional[int] = None
    @field_validator('email', mode='before')
    @classmethod
    def empty_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return v


class SubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None
    max_users: Optional[int] = None
    max_branches: Optional[int] = None

class CompanyOnboard(BaseModel):
    company_name: str
    admin_name: str
    admin_email: EmailStr
    admin_password: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None
    primary_branch_name: Optional[str] = "Main Branch"
    subscription_plan: Optional[str] = "pro"
    max_users: Optional[int] = None
    max_branches: Optional[int] = None

class CompanyOut(CompanyBase, AuditBase):
    branches_count: Optional[int] = None
    users_count: Optional[int] = None

