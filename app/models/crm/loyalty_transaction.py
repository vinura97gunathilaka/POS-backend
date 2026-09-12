from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class LoyaltyTransaction(Base, CompanyAuditMixin):
    __tablename__ = "loyalty_transactions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False) # can be positive (earned) or negative (redeemed)
    type = Column(String(50), nullable=False) # earn, redeem, adjust, expire
    reference_id = Column(String(100), nullable=True) # e.g. sale_id
    description = Column(String(255), nullable=True)

    customer = relationship("Customer", back_populates="loyalty_transactions")
