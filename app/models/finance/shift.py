from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class Shift(Base, BranchAuditMixin):
    __tablename__ = "shifts"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cash_drawer_id = Column(Integer, ForeignKey("cash_drawers.id", ondelete="CASCADE"), nullable=False)
    open_time = Column(DateTime(timezone=True), nullable=False)
    close_time = Column(DateTime(timezone=True), nullable=True)
    opening_balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    expected_cash = Column(Numeric(12, 2), default=0.00, nullable=False)
    actual_cash = Column(Numeric(12, 2), default=0.00, nullable=False)
    variance = Column(Numeric(12, 2), default=0.00, nullable=False)
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    user = relationship("User")
    cash_drawer = relationship("CashDrawer", back_populates="shifts")
    sales = relationship("Sale", back_populates="shift")
