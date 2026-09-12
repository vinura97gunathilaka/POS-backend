from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class Promotion(Base, BranchAuditMixin):
    __tablename__ = "promotions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True) # can be global across company if null
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False) # buy_one_get_one, percentage, flat_discount, seasonal
    value = Column(Numeric(12, 2), default=0.00, nullable=False) # discount percentage or amount
    min_cart_value = Column(Numeric(12, 2), default=0.00, nullable=False)
    coupon_code = Column(String(50), unique=True, index=True, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    company = relationship("Company")
