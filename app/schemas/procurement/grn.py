from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.crm import SupplierOut
from app.schemas.procurement.grn_item import GRNItemCreate, GRNItemOut

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
