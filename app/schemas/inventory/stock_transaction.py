from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class StockTransactionOut(AuditBase):
    company_id: int
    branch_id: int
    inventory_id: int
    product_variant_id: int
    quantity: int
    type: str  # sale, grn, adjustment, transfer_in, transfer_out, damage, expired
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    cost_at_transaction: Decimal

class StockAdjustmentPayload(BaseModel):
    branch_id: int
    product_variant_id: int
    quantity: int  # positive for in, negative for out
    type: str  # adjustment, damage, expired
    notes: Optional[str] = None
