from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.catalog import ProductVariantOut

# --- Inventory ---
class InventoryOut(AuditBase):
    company_id: int
    branch_id: int
    product_variant_id: int
    quantity: int
    avg_cost: Decimal
    location_bin: Optional[str] = None
    variant: Optional[ProductVariantOut] = None

# --- Stock Transaction ---
class StockTransactionOut(AuditBase):
    company_id: int
    branch_id: int
    inventory_id: int
    product_variant_id: int
    quantity: int
    type: str # sale, grn, adjustment, transfer_in, transfer_out, damage, expired
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    cost_at_transaction: Decimal

# --- Stock Transfer ---
class StockTransferItemBase(BaseModel):
    product_variant_id: int
    quantity_transferred: int

class StockTransferItemCreate(StockTransferItemBase):
    pass

class StockTransferItemOut(StockTransferItemBase, AuditBase):
    company_id: int
    stock_transfer_id: int
    quantity_received: int

class StockTransferBase(BaseModel):
    from_branch_id: int
    to_branch_id: int
    transfer_date: datetime
    notes: Optional[str] = None

class StockTransferCreate(StockTransferBase):
    company_id: int
    items: List[StockTransferItemCreate]

class StockTransferUpdate(BaseModel):
    status: Optional[str] = None # requested, transit, received, cancelled
    items_received: Optional[List[Dict[str, int]]] = None # [{"product_variant_id": 1, "quantity_received": 10}]
    notes: Optional[str] = None

class StockTransferOut(StockTransferBase, AuditBase):
    company_id: int
    total_items: int
    items: List[StockTransferItemOut] = []

# --- Manual Stock Adjustment ---
class StockAdjustmentPayload(BaseModel):
    branch_id: int
    product_variant_id: int
    quantity: int # positive for in, negative for out
    type: str # adjustment, damage, expired
    notes: Optional[str] = None

