from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class Voucher(Base, CompanyAuditMixin):
    __tablename__ = "vouchers"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    initial_value = Column(Numeric(12, 2), nullable=False)
    balance = Column(Numeric(12, 2), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company")
