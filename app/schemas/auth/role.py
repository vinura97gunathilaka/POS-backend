from typing import Optional, List
from pydantic import BaseModel
from app.schemas.auth.audit import AuditBase
from app.schemas.auth.permission import PermissionOut

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

class RolePermissionAssign(BaseModel):
    permission_ids: List[int]
