from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.catalog import ProductVariantOut

class GRNItemBase(BaseModel):
    product_variant_id: int
    quantity_received: int
    unit_cost: Decimal
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None

class GRNItemCreate(GRNItemBase):
    pass

class GRNItemOut(GRNItemBase, AuditBase):
    company_id: int
    branch_id: int
    grn_id: int
    total_cost: Decimal
    variant: Optional[ProductVariantOut] = None
