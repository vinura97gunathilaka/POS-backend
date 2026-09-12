from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class BankAccount(Base, BranchAuditMixin):
    __tablename__ = "bank_accounts"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True) # can be company level if null
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(100), nullable=False)
    account_holder = Column(String(100), nullable=True)
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)

    company = relationship("Company")
