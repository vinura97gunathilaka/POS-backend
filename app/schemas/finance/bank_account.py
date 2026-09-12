from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class BankAccountBase(BaseModel):
    bank_name: str
    account_number: str
    account_holder: Optional[str] = None
    balance: Decimal = Decimal("0.00")

class BankAccountCreate(BankAccountBase):
    company_id: int
    branch_id: Optional[int] = None

class BankAccountOut(BankAccountBase, AuditBase):
    company_id: int
    branch_id: Optional[int] = None
