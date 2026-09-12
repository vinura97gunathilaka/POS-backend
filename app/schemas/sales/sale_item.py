from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.catalog import ProductVariantOut

class SaleItemBase(BaseModel):
    product_variant_id: int
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemOut(SaleItemBase, AuditBase):
    company_id: int
    branch_id: int
    sale_id: int
    unit_cost: Decimal
    total_amount: Decimal
    variant: Optional[ProductVariantOut] = None
