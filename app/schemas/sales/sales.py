from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.organization import CompanyOut, BranchOut
from app.schemas.catalog import ProductVariantOut

# --- Sale Item ---
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


# --- Payment ---
class PaymentBase(BaseModel):
    amount: Decimal
    payment_method: str # cash, card, qr_payment, bank_transfer, credit, voucher
    transaction_reference: Optional[str] = None
    bank_account_id: Optional[int] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase, AuditBase):
    company_id: int
    branch_id: int
    sale_id: int

# --- Sale ---
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
    sale_status: Optional[str] = None # completed, held, cancelled, refunded
    payment_status: Optional[str] = None # paid, partial, unpaid, refunded
    preparation_status: Optional[str] = None # pending, preparing, ready, completed, none
    cancel_reason: Optional[str] = None

class CSATFeedbackOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    sale_id: int
    rating: int
    feedback_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CSATFeedbackCreate(BaseModel):
    rating: int
    feedback_text: Optional[str] = None

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




