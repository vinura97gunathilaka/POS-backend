from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class StockTransfer(Base, CompanyAuditMixin):
    __tablename__ = "stock_transfers"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    from_branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    to_branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    transfer_date = Column(DateTime(timezone=True), nullable=False)
    total_items = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="requested", nullable=False) # requested, transit, received, cancelled
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    from_branch = relationship("Branch", foreign_keys=[from_branch_id])
    to_branch = relationship("Branch", foreign_keys=[to_branch_id])
    items = relationship("StockTransferItem", back_populates="transfer", cascade="all, delete-orphan")
