from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class LoyaltyTransactionBase(BaseModel):
    points: int
    type: str  # earn, redeem, adjust, expire
    reference_id: Optional[str] = None
    description: Optional[str] = None

class LoyaltyTransactionOut(LoyaltyTransactionBase, AuditBase):
    company_id: int
    customer_id: int
