from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class LoyaltyRule(Base, CompanyAuditMixin):
    __tablename__ = "loyalty_rules"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    spend_amount = Column(Numeric(12, 2), default=100.00, nullable=False)  # Rs. 100
    points_earned = Column(Integer, default=1, nullable=False)            # 1 Point
    point_value = Column(Numeric(12, 2), default=1.00, nullable=False)     # 1 Point = Rs. 1

    company = relationship("Company")
