from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class LoyaltyRuleBase(BaseModel):
    name: str
    spend_amount: Decimal = Decimal("100.00")
    points_earned: int = 1
    point_value: Decimal = Decimal("1.00")

class LoyaltyRuleCreate(LoyaltyRuleBase):
    company_id: int

class LoyaltyRuleUpdate(BaseModel):
    name: Optional[str] = None
    spend_amount: Optional[Decimal] = None
    points_earned: Optional[int] = None
    point_value: Optional[Decimal] = None
    status: Optional[str] = None

class LoyaltyRuleOut(LoyaltyRuleBase, AuditBase):
    company_id: int
