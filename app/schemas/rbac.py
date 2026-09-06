from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Base Audit Fields Schema
class AuditBase(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    status: str = "active"

    class Config:
        from_attributes = True

# --- Company ---
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

# --- Branch ---
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

# --- Permission ---
class PermissionBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    company_id: int

class PermissionOut(PermissionBase, AuditBase):
    company_id: int

# --- Role ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    company_id: int
    permission_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    status: Optional[str] = None

class RoleOut(RoleBase, AuditBase):
    company_id: int
    permissions: List[PermissionOut] = []

# --- User ---
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

class UserOut(UserBase, AuditBase):
    company_id: int
    company: Optional[CompanyOut] = None
    roles: List[RoleOut] = []
    branches: List[BranchOut] = []
