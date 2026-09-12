from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

# Import sibling models for backward-compatibility re-export
from app.models.inventory.stock_transaction import StockTransaction
from app.models.inventory.stock_transfer import StockTransfer
from app.models.inventory.stock_transfer_item import StockTransferItem

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

__all__ = ["Inventory", "StockTransaction", "StockTransfer", "StockTransferItem"]
