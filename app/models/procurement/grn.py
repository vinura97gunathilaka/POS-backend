from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class GRN(Base, BranchAuditMixin):
    __tablename__ = "grns"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    receive_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    invoice_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    purchase = relationship("Purchase", back_populates="grns")
    supplier = relationship("Supplier")
    items = relationship("GRNItem", back_populates="grn", cascade="all, delete-orphan")
