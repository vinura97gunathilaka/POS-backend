from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.marketing.voucher import Voucher
from app.schemas.marketing.voucher import VoucherCreate
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/vouchers/validate", response_model=APIResponse[dict])
def validate_voucher(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    voucher = db.query(Voucher).filter(
        Voucher.code == code,
        Voucher.company_id == current_user.company_id
    ).first()
    
    if not voucher:
        raise HTTPException(status_code=404, detail="Invalid voucher code")
        
    if voucher.expiry_date and voucher.expiry_date < now:
        raise HTTPException(status_code=400, detail="Voucher has expired")
        
    if float(voucher.balance) <= 0:
        raise HTTPException(status_code=400, detail="Voucher has zero balance")
        
    return APIResponse(data={
        "id": voucher.id,
        "code": voucher.code,
        "name": voucher.name,
        "balance": float(voucher.balance)
    })

@router.get("/vouchers", response_model=APIResponse[List[dict]])
def list_vouchers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vouchers = db.query(Voucher).filter(Voucher.company_id == current_user.company_id).all()
    res = []
    for v in vouchers:
        res.append({
            "id": v.id,
            "code": v.code,
            "name": v.name,
            "initial_value": float(v.initial_value),
            "balance": float(v.balance),
            "expiry_date": v.expiry_date.isoformat() if v.expiry_date else None
        })
    return APIResponse(data=res)

@router.post("/vouchers", response_model=APIResponse[dict])
def create_voucher(
    payload: VoucherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Voucher).filter(
        Voucher.code == payload.code,
        Voucher.company_id == current_user.company_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Voucher code already registered")
        
    voucher = Voucher(
        company_id=current_user.company_id,
        code=payload.code,
        name=payload.name,
        initial_value=payload.initial_value,
        balance=payload.initial_value,
        expiry_date=payload.expiry_date,
        status="active"
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    return APIResponse(data={"id": voucher.id, "code": voucher.code})
