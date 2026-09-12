from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class StockTransferItem(Base, CompanyAuditMixin):
    __tablename__ = "stock_transfer_items"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    stock_transfer_id = Column(Integer, ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity_transferred = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0, nullable=False)

    transfer = relationship("StockTransfer", back_populates="items")
    variant = relationship("ProductVariant")
