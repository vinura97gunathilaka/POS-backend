from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class Category(Base, CompanyAuditMixin):
    __tablename__ = "categories"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    company = relationship("Company")
    parent = relationship("Category", remote_side="Category.id", backref="children")
    products = relationship("Product", back_populates="category")

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

class ProductVariantComponent(Base, CompanyAuditMixin):
    __tablename__ = "product_variant_components"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    parent_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    component_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    company = relationship("Company")
    parent_variant = relationship(
        "ProductVariant", 
        foreign_keys=[parent_variant_id], 
        back_populates="recipe_components"
    )
    component_variant = relationship(
        "ProductVariant", 
        foreign_keys=[component_variant_id]
    )

