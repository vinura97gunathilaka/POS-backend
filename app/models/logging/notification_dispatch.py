from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class NotificationDispatch(Base, CompanyAuditMixin):
    __tablename__ = "notification_dispatches"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False) # "email", "whatsapp"
    recipient = Column(String(255), nullable=False)
    dispatch_status = Column(String(50), default="sent", nullable=False) # "sent", "failed"
    error_message = Column(Text, nullable=True)

    company = relationship("Company")
    branch = relationship("Branch")
    sale = relationship("Sale")
