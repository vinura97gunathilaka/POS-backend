from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class Sale(Base, BranchAuditMixin):
    __tablename__ = "sales"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False) # Cashier
    shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    sale_date = Column(DateTime(timezone=True), nullable=False)
    sub_total = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    loyalty_points_redeemed = Column(Integer, default=0, nullable=False)
    loyalty_discount = Column(Numeric(12, 2), default=0.00, nullable=False)
    net_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    amount_paid = Column(Numeric(12, 2), default=0.00, nullable=False)
    change_returned = Column(Numeric(12, 2), default=0.00, nullable=False)
    payment_status = Column(String(50), default="unpaid", nullable=False) # paid, partial, unpaid, refunded
    sale_status = Column(String(50), default="completed", nullable=False)   # completed, held, cancelled, refunded
    preparation_status = Column(String(50), default="none", nullable=True) # none, pending, preparing, ready, completed
    notes = Column(Text, nullable=True)
    hold_reference = Column(String(100), nullable=True)

    company = relationship("Company")
    branch = relationship("Branch")
    customer = relationship("Customer")
    cashier = relationship("User")
    shift = relationship("Shift", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan")
    csat_feedback = relationship("CSATFeedback", uselist=False, back_populates="sale", cascade="all, delete-orphan")
