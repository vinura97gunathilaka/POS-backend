from typing import Optional
from app.schemas.auth import AuditBase

class NotificationOut(AuditBase):
    company_id: int
    branch_id: Optional[int] = None
    title: str
    message: str
    type: str  # low_stock, shift_alert, transfer_alert, loyalty_expiry, system
    is_read: bool
