from typing import Optional
from app.schemas.auth import AuditBase

class NotificationDispatchOut(AuditBase):
    company_id: int
    branch_id: int
    sale_id: int
    type: str
    recipient: str
    dispatch_status: str
    error_message: Optional[str] = None
