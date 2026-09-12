from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class ProductVariant(Base, CompanyAuditMixin):
    __tablename__ = "product_variants"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False) # e.g. "Size: M / Color: Blue"
    sku = Column(String(100), unique=True, index=True, nullable=True)
    barcode = Column(String(100), index=True, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    cost = Column(Numeric(12, 2), nullable=False)
    attributes = Column(JSON, default=dict, nullable=False) # e.g. {"size": "M", "color": "Blue"}

    product = relationship("Product", back_populates="variants")
    inventories = relationship("Inventory", back_populates="variant", cascade="all, delete-orphan")
    recipe_components = relationship(
        "ProductVariantComponent", 
        foreign_keys="[ProductVariantComponent.parent_variant_id]", 
        cascade="all, delete-orphan", 
        back_populates="parent_variant"
    )
