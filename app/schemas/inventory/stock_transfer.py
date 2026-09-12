from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase

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
    status: Optional[str] = None  # requested, transit, received, cancelled
    items_received: Optional[List[Dict[str, int]]] = None  # [{"product_variant_id": 1, "quantity_received": 10}]
    notes: Optional[str] = None

class StockTransferOut(StockTransferBase, AuditBase):
    company_id: int
    total_items: int
    items: List[StockTransferItemOut] = []
