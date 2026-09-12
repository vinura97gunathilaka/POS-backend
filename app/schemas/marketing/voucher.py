from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class VoucherBase(BaseModel):
    code: str
    name: Optional[str] = None
    initial_value: Decimal
    expiry_date: Optional[datetime] = None

class VoucherCreate(VoucherBase):
    company_id: Optional[int] = None

class VoucherOut(VoucherBase):
    id: int
    company_id: int
    balance: Decimal
    status: Optional[str] = "active"

    class Config:
        from_attributes = True
