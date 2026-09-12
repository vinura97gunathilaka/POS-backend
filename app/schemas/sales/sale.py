from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.organization import CompanyOut, BranchOut
from app.schemas.sales.sale_item import SaleItemCreate, SaleItemOut
from app.schemas.sales.payment import PaymentCreate, PaymentOut
from app.schemas.sales.csat_feedback import CSATFeedbackOut

class SaleBase(BaseModel):
    customer_id: Optional[int] = None
    sub_total: Decimal
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    loyalty_points_redeemed: int = 0
    loyalty_discount: Decimal = Decimal("0.00")
    net_amount: Decimal
    amount_paid: Decimal
    change_returned: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    hold_reference: Optional[str] = None
    shift_id: Optional[int] = None
    preparation_status: Optional[str] = "none"

class SaleCreate(SaleBase):
    company_id: int
    branch_id: int
    items: List[SaleItemCreate]
    payments: List[PaymentCreate]

class SaleUpdate(BaseModel):
    sale_status: Optional[str] = None  # completed, held, cancelled, refunded
    payment_status: Optional[str] = None  # paid, partial, unpaid, refunded
    preparation_status: Optional[str] = None  # pending, preparing, ready, completed, none
    cancel_reason: Optional[str] = None

class SaleOut(SaleBase, AuditBase):
    company_id: int
    branch_id: int
    user_id: int
    invoice_number: str
    sale_date: datetime
    payment_status: str
    sale_status: str
    items: List[SaleItemOut] = []
    payments: List[PaymentOut] = []
    company: Optional[CompanyOut] = None
    branch: Optional[BranchOut] = None
    csat_feedback: Optional[CSATFeedbackOut] = None

class ReceiptDispatchPayload(BaseModel):
    type: str  # "email" or "whatsapp"
    recipient: str
