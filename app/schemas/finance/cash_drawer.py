from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class CashDrawerBase(BaseModel):
    name: str
    balance: Decimal = Decimal("0.00")

class CashDrawerCreate(CashDrawerBase):
    company_id: int
    branch_id: int

class CashDrawerOut(CashDrawerBase, AuditBase):
    company_id: int
    branch_id: int
