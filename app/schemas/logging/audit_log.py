from typing import Optional, Any
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class AuditLogOut(AuditBase):
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    model_name: Optional[str] = None
    record_id: Optional[str] = None
    old_data: Optional[Any] = None
    new_data: Optional[Any] = None
    changes: Optional[Any] = None
    details: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None

class AuditStatsOut(BaseModel):
    total_events: int
    actions: dict
    top_models: dict
    top_operators: dict
