import re
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.auth.audit import AuditBase
from app.schemas.organization import CompanyOut
from app.schemas.organization import BranchOut
from app.schemas.auth.role import RoleOut

class UserBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    employee_id: Optional[str] = None
    nic: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_superadmin: bool = False
    has_system_access: bool = True
    must_change_password: bool = False

class UserCreate(UserBase):
    company_id: Optional[int] = None
    password: Optional[str] = None
    role_ids: Optional[List[int]] = []
    branch_ids: Optional[List[int]] = []

    @field_validator("nic")
    @classmethod
    def validate_nic(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        v_clean = v.strip().upper()
        # Old format: 9 digits + 'V' or 'X'. New format: 12 digits.
        old_pattern = r"^\d{9}[VX]$"
        new_pattern = r"^\d{12}$"
        if not (re.match(old_pattern, v_clean) or re.match(new_pattern, v_clean)):
            raise ValueError("Invalid NIC format. Must be 9 digits + 'V'/'X' (e.g. 901234567V) or 12 digits (e.g. 199012345678).")
        return v_clean

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    employee_id: Optional[str] = None
    nic: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    password: Optional[str] = None
    has_system_access: Optional[bool] = None
    must_change_password: Optional[bool] = None
    role_ids: Optional[List[int]] = None
    branch_ids: Optional[List[int]] = None
    status: Optional[str] = None

class UserRoleAssign(BaseModel):
    role_ids: List[int]

class UserOut(UserBase, AuditBase):
    company_id: Optional[int] = None
    company: Optional[CompanyOut] = None
    roles: List[RoleOut] = []
    branches: List[BranchOut] = []
