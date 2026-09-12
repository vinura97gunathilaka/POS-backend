from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class Notification(Base, BranchAuditMixin):
    __tablename__ = "notifications"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True) # can be global
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False) # low_stock, shift_alert, transfer_alert, loyalty_expiry, system
    is_read = Column(Boolean, default=False, nullable=False)

    company = relationship("Company")
