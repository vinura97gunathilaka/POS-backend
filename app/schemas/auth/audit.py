from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class AuditBase(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    status: str = "active"

    class Config:
        from_attributes = True
