from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class ProductVariantComponent(Base, CompanyAuditMixin):
    __tablename__ = "product_variant_components"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    parent_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    component_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    company = relationship("Company")
    parent_variant = relationship("ProductVariant", foreign_keys=[parent_variant_id], back_populates="recipe_components")
    component_variant = relationship("ProductVariant", foreign_keys=[component_variant_id])
