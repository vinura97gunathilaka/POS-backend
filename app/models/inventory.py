from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin, CompanyAuditMixin

class Inventory(Base, BranchAuditMixin):
    __tablename__ = "inventories"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    avg_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    location_bin = Column(String(100), nullable=True)

    company = relationship("Company")
    variant = relationship("ProductVariant", back_populates="inventories")
    transactions = relationship("StockTransaction", back_populates="inventory", cascade="all, delete-orphan")

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

class StockTransferItem(Base, CompanyAuditMixin):
    __tablename__ = "stock_transfer_items"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    stock_transfer_id = Column(Integer, ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity_transferred = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0, nullable=False)

    transfer = relationship("StockTransfer", back_populates="items")
    variant = relationship("ProductVariant")
