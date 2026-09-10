from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin, CompanyAuditMixin

class Notification(Base, BranchAuditMixin):
    __tablename__ = "notifications"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True) # can be global
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False) # low_stock, shift_alert, transfer_alert, loyalty_expiry, system
    is_read = Column(Boolean, default=False, nullable=False)

    company = relationship("Company")

class AuditLog(Base, CompanyAuditMixin):
    __tablename__ = "audit_logs"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False, index=True) # e.g. "login", "sale_cancel"
    details = Column(JSON, nullable=True) # e.g. {"sale_id": 4, "reason": "Wrong item"}
    ip_address = Column(String(50), nullable=True)

    company = relationship("Company")
    user = relationship("User")

    @property
    def user_name(self) -> str:
        return self.user.name if self.user else "System"

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

