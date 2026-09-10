from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.crm import SupplierOut
from app.schemas.catalog import ProductVariantOut

# --- Purchase Items ---
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

# --- Purchases ---
class PurchaseBase(BaseModel):
    supplier_id: int
    order_date: datetime
    expected_delivery: Optional[datetime] = None
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    notes: Optional[str] = None

class PurchaseCreate(PurchaseBase):
    company_id: int
    branch_id: int
    items: List[PurchaseItemCreate]

class PurchaseOut(PurchaseBase, AuditBase):
    company_id: int
    branch_id: int
    total_amount: Decimal
    net_amount: Decimal
    items: List[PurchaseItemOut] = []
    supplier: Optional[SupplierOut] = None

# --- GRN Items ---
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

# --- GRN ---
class GRNBase(BaseModel):
    purchase_id: Optional[int] = None
    supplier_id: int
    receive_date: datetime
    invoice_number: Optional[str] = None
    notes: Optional[str] = None

class GRNCreate(GRNBase):
    company_id: int
    branch_id: int
    items: List[GRNItemCreate]

class GRNOut(GRNBase, AuditBase):
    company_id: int
    branch_id: int
    total_amount: Decimal
    items: List[GRNItemOut] = []
    supplier: Optional[SupplierOut] = None

