from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class PurchaseItemBase(BaseModel):
    product_variant_id: int
    quantity: int
    unit_cost: Decimal

class PurchaseItemCreate(PurchaseItemBase):
    pass

class PurchaseItemOut(PurchaseItemBase, AuditBase):
    company_id: int
    branch_id: int
    purchase_id: int
    total_cost: Decimal
