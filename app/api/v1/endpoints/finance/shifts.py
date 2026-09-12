from typing import List
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.sales.sale import Sale
from app.models.sales.payment import Payment
from app.models.finance.cash_drawer import CashDrawer
from app.models.finance.shift import Shift
from app.models.logging.audit_log import AuditLog
from app.schemas.finance.shift import ShiftCreate, ShiftOut, ShiftUpdate
from app.schemas.response import APIResponse

router = APIRouter()

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

    drawer = db.query(CashDrawer).filter(CashDrawer.id == payload.cash_drawer_id).first()
    if not drawer:
        raise HTTPException(status_code=404, detail="Cash drawer not found")

    drawer.balance = payload.opening_balance

    shift = Shift(
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        user_id=current_user.id,
        cash_drawer_id=payload.cash_drawer_id,
        open_time=datetime.now(timezone.utc),
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

    x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request and request.client else None)
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
    shift.close_time = datetime.now(timezone.utc)
    shift.status = "closed"
    if payload.notes:
        shift.notes = f"{shift.notes or ''} [Close info: {payload.notes}]"
    shift.updated_by = current_user.id

    drawer = db.query(CashDrawer).filter(CashDrawer.id == shift.cash_drawer_id).first()
    if drawer:
        drawer.balance = actual

    x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request and request.client else None)
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
