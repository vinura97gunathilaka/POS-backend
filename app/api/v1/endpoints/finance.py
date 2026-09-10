from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.sales import Payment, Sale
from app.models.finance import ExpenseCategory, Expense, BankAccount, CashDrawer, Shift
from app.schemas.finance import (
    ExpenseCategoryCreate, ExpenseCategoryOut,
    ExpenseCreate, ExpenseOut,
    BankAccountCreate, BankAccountOut,
    CashDrawerCreate, CashDrawerOut,
    ShiftCreate, ShiftOut, ShiftUpdate
)
from app.schemas.response import APIResponse

router = APIRouter()

# --- Shifts Management ---
@router.get("/shifts", response_model=APIResponse[List[ShiftOut]])
def list_shifts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Shift)
    if not current_user.is_superadmin:
        query = query.filter(Shift.company_id == current_user.company_id)
    shifts = query.all()
    return APIResponse(data=shifts)

@router.post("/shifts", response_model=APIResponse[ShiftOut])
def open_shift(
    payload: ShiftCreate,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if cashier already has an open shift in this branch
    active_shift = db.query(Shift).filter(
        Shift.user_id == current_user.id,
        Shift.branch_id == payload.branch_id,
        Shift.status == "open"
    ).first()

    if active_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active open shift in this branch. Close it first."
        )

    # Verify cash drawer exists and reset balance to opening balance
    drawer = db.query(CashDrawer).filter(CashDrawer.id == payload.cash_drawer_id).first()
    if not drawer:
        raise HTTPException(status_code=404, detail="Cash drawer not found")

    drawer.balance = payload.opening_balance

    shift = Shift(
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        user_id=current_user.id,
        cash_drawer_id=payload.cash_drawer_id,
        open_time=datetime.utcnow(),
        opening_balance=payload.opening_balance,
        expected_cash=payload.opening_balance,
        actual_cash=Decimal("0.00"),
        variance=Decimal("0.00"),
        notes=payload.notes,
        status="open",
        created_by=current_user.id
    )
    db.add(shift)
    db.flush()

    # Log Audit Log
    x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request and request.client else None)
    from app.models.logging import AuditLog
    db.add(AuditLog(
        company_id=payload.company_id,
        user_id=current_user.id,
        action="shift_open",
        details={
            "shift_id": shift.id,
            "opening_balance": float(payload.opening_balance)
        },
        ip_address=ip_address
    ))

    db.commit()
    db.refresh(shift)
    return APIResponse(data=shift)

@router.put("/shifts/{id}/close", response_model=APIResponse[ShiftOut])
def close_shift(
    id: int,
    payload: ShiftUpdate,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shift = db.query(Shift).filter(Shift.id == id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    if shift.status == "closed":
        raise HTTPException(status_code=400, detail="Shift is already closed")

    # Compute expected cash = opening_balance + sum of cash payments in this shift
    cash_payments = db.query(func.sum(Payment.amount)).join(Sale).filter(
        Sale.shift_id == shift.id,
        Payment.payment_method == "cash",
        Sale.sale_status == "completed"
    ).scalar() or Decimal("0.00")

    expected = shift.opening_balance + cash_payments
    actual = payload.actual_cash if payload.actual_cash is not None else Decimal("0.00")
    variance = actual - expected

    shift.expected_cash = expected
    shift.actual_cash = actual
    shift.variance = variance
    shift.close_time = datetime.utcnow()
    shift.status = "closed"
    if payload.notes:
        shift.notes = f"{shift.notes or ''} [Close info: {payload.notes}]"
    shift.updated_by = current_user.id

    # Update Cash Drawer balance
    drawer = db.query(CashDrawer).filter(CashDrawer.id == shift.cash_drawer_id).first()
    if drawer:
        drawer.balance = actual

    # Log Audit Log
    x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request and request.client else None)
    from app.models.logging import AuditLog
    db.add(AuditLog(
        company_id=shift.company_id,
        user_id=current_user.id,
        action="shift_close",
        details={
            "shift_id": shift.id,
            "expected_cash": float(expected),
            "actual_cash": float(actual),
            "variance": float(variance)
        },
        ip_address=ip_address
    ))

    db.commit()
    db.refresh(shift)
    return APIResponse(data=shift)

# --- Expense Management ---
@router.get("/expenses/categories", response_model=APIResponse[List[ExpenseCategoryOut]])
def list_expense_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ExpenseCategory).filter(ExpenseCategory.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(ExpenseCategory.company_id == current_user.company_id)
    categories = query.all()
    return APIResponse(data=categories)

@router.post("/expenses/categories", response_model=APIResponse[ExpenseCategoryOut])
def create_expense_category(
    payload: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = ExpenseCategory(**payload.dict(), created_by=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return APIResponse(data=category)

@router.get("/expenses", response_model=APIResponse[List[ExpenseOut]])
def list_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Expense).filter(Expense.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Expense.company_id == current_user.company_id)
    expenses = query.all()
    return APIResponse(data=expenses)

@router.post("/expenses", response_model=APIResponse[ExpenseOut])
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = Expense(**payload.dict(), created_by=current_user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return APIResponse(data=expense)

# --- Bank Accounts ---
@router.get("/bank-accounts", response_model=APIResponse[List[BankAccountOut]])
def list_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(BankAccount).filter(BankAccount.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(BankAccount.company_id == current_user.company_id)
    accounts = query.all()
    return APIResponse(data=accounts)

@router.post("/bank-accounts", response_model=APIResponse[BankAccountOut])
def create_bank_account(
    payload: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = BankAccount(**payload.dict(), created_by=current_user.id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return APIResponse(data=account)

# --- Cash Drawer ---
@router.get("/cash-drawers", response_model=APIResponse[List[CashDrawerOut]])
def list_cash_drawers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CashDrawer).filter(CashDrawer.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(CashDrawer.company_id == current_user.company_id)
    drawers = query.all()
    return APIResponse(data=drawers)

@router.post("/cash-drawers", response_model=APIResponse[CashDrawerOut])
def create_cash_drawer(
    payload: CashDrawerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    drawer = CashDrawer(**payload.dict(), created_by=current_user.id)
    db.add(drawer)
    db.commit()
    db.refresh(drawer)
    return APIResponse(data=drawer)

