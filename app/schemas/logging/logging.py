from typing import Optional, Any
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class NotificationOut(AuditBase):
    company_id: int
    branch_id: Optional[int] = None
    title: str
    message: str
    type: str # low_stock, shift_alert, transfer_alert, loyalty_expiry, system
    is_read: bool

class AuditLogOut(AuditBase):
    company_id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    details: Optional[Any] = None
    ip_address: Optional[str] = None

class NotificationDispatchOut(AuditBase):
    company_id: int
    branch_id: int
    sale_id: int
    type: str
    recipient: str
    dispatch_status: str
    error_message: Optional[str] = None


