from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin, CompanyAuditMixin

class ExpenseCategory(Base, CompanyAuditMixin):
    __tablename__ = "expense_categories"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    company = relationship("Company")

class Expense(Base, BranchAuditMixin):
    __tablename__ = "expenses"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("expense_categories.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(500), nullable=True)
    approved_by = Column(Integer, nullable=True) # Linked to user id

    company = relationship("Company")
    category = relationship("ExpenseCategory")

class BankAccount(Base, BranchAuditMixin):
    __tablename__ = "bank_accounts"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True) # can be company level if null
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(100), nullable=False)
    account_holder = Column(String(100), nullable=True)
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)

    company = relationship("Company")

class CashDrawer(Base, BranchAuditMixin):
    __tablename__ = "cash_drawers"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False) # e.g. "Drawer 1"
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)

    company = relationship("Company")
    shifts = relationship("Shift", back_populates="cash_drawer")

class Shift(Base, BranchAuditMixin):
    __tablename__ = "shifts"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cash_drawer_id = Column(Integer, ForeignKey("cash_drawers.id", ondelete="CASCADE"), nullable=False)
    open_time = Column(DateTime(timezone=True), nullable=False)
    close_time = Column(DateTime(timezone=True), nullable=True)
    opening_balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    expected_cash = Column(Numeric(12, 2), default=0.00, nullable=False)
    actual_cash = Column(Numeric(12, 2), default=0.00, nullable=False)
    variance = Column(Numeric(12, 2), default=0.00, nullable=False)
    notes = Column(Text, nullable=True)

    company = relationship("Company")
    user = relationship("User")
    cash_drawer = relationship("CashDrawer", back_populates="shifts")
    sales = relationship("Sale", back_populates="shift")
