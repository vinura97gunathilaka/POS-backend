from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.crm import SupplierOut
from app.schemas.procurement.purchase_item import PurchaseItemCreate, PurchaseItemOut

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
