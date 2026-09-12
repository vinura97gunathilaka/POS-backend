from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class PromotionBase(BaseModel):
    name: str
    type: str  # percentage, flat_discount, buy_one_get_one, seasonal
    value: Decimal
    min_cart_value: Decimal = Decimal("0.00")
    coupon_code: Optional[str] = None
    start_date: datetime
    end_date: datetime

class PromotionCreate(PromotionBase):
    company_id: Optional[int] = None
    branch_id: Optional[int] = None

class PromotionOut(PromotionBase):
    id: int
    company_id: int
    branch_id: Optional[int] = None
    status: Optional[str] = "active"

    class Config:
        from_attributes = True
