from typing import Optional
from datetime import datetime
from pydantic import BaseModel

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
