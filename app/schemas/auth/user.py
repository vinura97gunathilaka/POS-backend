from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.schemas.auth.audit import AuditBase
from app.schemas.organization import CompanyOut
from app.schemas.organization import BranchOut
from app.schemas.auth.role import RoleOut

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    is_superadmin: bool = False

class UserCreate(UserBase):
    company_id: int
    password: str
    role_ids: Optional[List[int]] = []
    branch_ids: Optional[List[int]] = []

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role_ids: Optional[List[int]] = None
    branch_ids: Optional[List[int]] = None
    status: Optional[str] = None

class UserRoleAssign(BaseModel):
    role_ids: List[int]

class UserOut(UserBase, AuditBase):
    company_id: int
    company: Optional[CompanyOut] = None
    roles: List[RoleOut] = []
    branches: List[BranchOut] = []
