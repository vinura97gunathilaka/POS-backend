from typing import Optional
from decimal import Decimal
from app.schemas.auth import AuditBase
from app.schemas.catalog import ProductVariantOut

# Import sibling schemas for backward-compatibility re-export
from app.schemas.inventory.stock_transaction import (
    StockTransactionOut,
    StockAdjustmentPayload,
)
from app.schemas.inventory.stock_transfer import (
    StockTransferItemBase,
    StockTransferItemCreate,
    StockTransferItemOut,
    StockTransferBase,
    StockTransferCreate,
    StockTransferUpdate,
    StockTransferOut,
)

class InventoryOut(AuditBase):
    company_id: int
    branch_id: int
    product_variant_id: int
    quantity: int
    avg_cost: Decimal
    location_bin: Optional[str] = None
    variant: Optional[ProductVariantOut] = None

__all__ = [
    "InventoryOut",
    "StockTransactionOut",
    "StockAdjustmentPayload",
    "StockTransferItemBase",
    "StockTransferItemCreate",
    "StockTransferItemOut",
    "StockTransferBase",
    "StockTransferCreate",
    "StockTransferUpdate",
    "StockTransferOut",
]
