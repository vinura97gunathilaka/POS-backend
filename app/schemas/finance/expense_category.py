from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class ExpenseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpenseCategoryCreate(ExpenseCategoryBase):
    company_id: int

class ExpenseCategoryOut(ExpenseCategoryBase, AuditBase):
    company_id: int
