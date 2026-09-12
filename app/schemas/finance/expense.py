from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class ExpenseBase(BaseModel):
    category_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    company_id: int
    branch_id: int

class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    approved_by: Optional[int] = None
    status: Optional[str] = None

class ExpenseOut(ExpenseBase, AuditBase):
    company_id: int
    branch_id: int
    approved_by: Optional[int] = None
