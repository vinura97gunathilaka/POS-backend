from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class Customer(Base, CompanyAuditMixin):
    __tablename__ = "customers"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True, nullable=True)
    phone = Column(String(50), index=True, nullable=True)
    address = Column(String(500), nullable=True)
    credit_limit = Column(Numeric(12, 2), default=0.00, nullable=False)
    balance = Column(Numeric(12, 2), default=0.00, nullable=False) # positive means customer owes money
    points = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="customer", cascade="all, delete-orphan")

class Supplier(Base, CompanyAuditMixin):
    __tablename__ = "suppliers"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    ledger_balance = Column(Numeric(12, 2), default=0.00, nullable=False)

    company = relationship("Company")

class LoyaltyRule(Base, CompanyAuditMixin):
    __tablename__ = "loyalty_rules"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    spend_amount = Column(Numeric(12, 2), default=100.00, nullable=False)  # Rs. 100
    points_earned = Column(Integer, default=1, nullable=False)            # 1 Point
    point_value = Column(Numeric(12, 2), default=1.00, nullable=False)     # 1 Point = Rs. 1

    company = relationship("Company")

class LoyaltyTransaction(Base, CompanyAuditMixin):
    __tablename__ = "loyalty_transactions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False) # can be positive (earned) or negative (redeemed)
    type = Column(String(50), nullable=False) # earn, redeem, adjust, expire
    reference_id = Column(String(100), nullable=True) # e.g. sale_id
    description = Column(String(255), nullable=True)

    customer = relationship("Customer", back_populates="loyalty_transactions")
