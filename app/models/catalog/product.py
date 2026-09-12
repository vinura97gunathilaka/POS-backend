from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class Product(Base, CompanyAuditMixin):
    __tablename__ = "products"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    sku = Column(String(100), unique=True, index=True, nullable=True)
    barcode = Column(String(100), index=True, nullable=True)
    qr_code = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)
    tax_rate = Column(Numeric(5, 2), default=0.00, nullable=False)  # e.g. 15.00 for 15%
    type = Column(String(50), default="product", nullable=False)   # product, service, combo
    track_inventory = Column(Boolean, default=True, nullable=False)
    reorder_level = Column(Integer, default=10, nullable=False)

    company = relationship("Company")
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
