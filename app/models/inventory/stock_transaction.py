from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class StockTransaction(Base, BranchAuditMixin):
    __tablename__ = "stock_transactions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("inventories.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)  # negative for stock outs
    type = Column(String(50), nullable=False)     # sale, grn, adjustment, transfer_in, transfer_out, damage, expired
    reference_id = Column(String(100), nullable=True) # ID of Sale, GRN, Transfer, or Adjustment
    reference_type = Column(String(50), nullable=True) # "sale", "grn", "transfer", "adjustment"
    cost_at_transaction = Column(Numeric(12, 2), nullable=False)

    inventory = relationship("Inventory", back_populates="transactions")
    variant = relationship("ProductVariant")
