from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    company_id: int

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    status: Optional[str] = None

class CategoryOut(CategoryBase, AuditBase):
    company_id: int
