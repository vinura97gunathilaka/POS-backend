from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class Purchase(Base, BranchAuditMixin):
    __tablename__ = "purchases"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    expected_delivery = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    net_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    supplier = relationship("Supplier")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    grns = relationship("GRN", back_populates="purchase")

class PurchaseItem(Base, BranchAuditMixin):
    __tablename__ = "purchase_items"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchase", back_populates="items")
    variant = relationship("ProductVariant")

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

class GRNItem(Base, BranchAuditMixin):
    __tablename__ = "grn_items"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    grn_id = Column(Integer, ForeignKey("grns.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity_received = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    grn = relationship("GRN", back_populates="items")
    variant = relationship("ProductVariant")
