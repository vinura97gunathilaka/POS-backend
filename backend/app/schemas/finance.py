from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.schemas.rbac import AuditBase

# --- Expense Category ---
class ExpenseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ExpenseCategoryCreate(ExpenseCategoryBase):
    company_id: int

class ExpenseCategoryOut(ExpenseCategoryBase, AuditBase):
    company_id: int

# --- Expense ---
class ExpenseBase(BaseModel):
    category_id: int
    amount: Decimal
    date: datetime
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    company_id: int
    branch_id: int

class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    approved_by: Optional[int] = None
    status: Optional[str] = None

class ExpenseOut(ExpenseBase, AuditBase):
    company_id: int
    branch_id: int
    approved_by: Optional[int] = None

# --- Bank Account ---
class BankAccountBase(BaseModel):
    bank_name: str
    account_number: str
    account_holder: Optional[str] = None
    balance: Decimal = Decimal("0.00")

class BankAccountCreate(BankAccountBase):
    company_id: int
    branch_id: Optional[int] = None

class BankAccountOut(BankAccountBase, AuditBase):
    company_id: int
    branch_id: Optional[int] = None

# --- Cash Drawer ---
class CashDrawerBase(BaseModel):
    name: str
    balance: Decimal = Decimal("0.00")

class CashDrawerCreate(CashDrawerBase):
    company_id: int
    branch_id: int

class CashDrawerOut(CashDrawerBase, AuditBase):
    company_id: int
    branch_id: int

# --- Shift ---
class ShiftBase(BaseModel):
    cash_drawer_id: int
    opening_balance: Decimal = Decimal("0.00")
    notes: Optional[str] = None

class ShiftCreate(ShiftBase):
    company_id: int
    branch_id: int

class ShiftUpdate(BaseModel):
    close_time: Optional[datetime] = None
    actual_cash: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None # open, closed

class ShiftOut(AuditBase):
    company_id: int
    branch_id: int
    user_id: int
    cash_drawer_id: int
    open_time: datetime
    close_time: Optional[datetime] = None
    opening_balance: Decimal
    expected_cash: Decimal
    actual_cash: Decimal
    variance: Decimal
    notes: Optional[str] = None
