from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class PaymentBase(BaseModel):
    amount: Decimal
    payment_method: str  # cash, card, qr_payment, bank_transfer, credit, voucher
    transaction_reference: Optional[str] = None
    bank_account_id: Optional[int] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase, AuditBase):
    company_id: int
    branch_id: int
    sale_id: int
