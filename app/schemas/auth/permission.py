from typing import Optional
from pydantic import BaseModel
from app.schemas.auth.audit import AuditBase

class PermissionBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    company_id: int

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class PermissionOut(PermissionBase, AuditBase):
    company_id: int
