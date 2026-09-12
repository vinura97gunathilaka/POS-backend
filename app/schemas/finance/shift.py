from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class ShiftBase(BaseModel):
    cash_drawer_id: int
    opening_balance: Decimal = Decimal("0.00")
    notes: Optional[str] = None

class ShiftCreate(ShiftBase):
    company_id: int
    branch_id: int

class ShiftUpdate(BaseModel):
    close_time: Optional[datetime] = None
    actual_cash: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # open, closed

class ShiftOut(AuditBase):
    company_id: int
    branch_id: int
    user_id: int
    cash_drawer_id: int
    open_time: datetime
    close_time: Optional[datetime] = None
    opening_balance: Decimal
    expected_cash: Decimal
    actual_cash: Decimal
    variance: Decimal
    notes: Optional[str] = None
