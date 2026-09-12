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
