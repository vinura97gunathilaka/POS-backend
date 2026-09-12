from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
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
    admin_password: str
    phone: Optional[str] = None
    primary_branch_name: Optional[str] = "Main Branch"
    subscription_plan: Optional[str] = "pro"
    max_users: Optional[int] = None
    max_branches: Optional[int] = None

class CompanyOut(CompanyBase, AuditBase):
    pass
