from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class CashDrawer(Base, BranchAuditMixin):
    __tablename__ = "cash_drawers"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False) # e.g. "Drawer 1"
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)

    company = relationship("Company")
    shifts = relationship("Shift", back_populates="cash_drawer")
