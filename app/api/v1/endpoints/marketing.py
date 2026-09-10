from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.marketing import Promotion, Voucher
from app.schemas.response import APIResponse

router = APIRouter()

# --- Schemas ---
class PromotionCreate(BaseModel):
    name: str
    type: str  # percentage or flat_discount
    value: float
    min_cart_value: float = 0.0
    coupon_code: str
    start_date: datetime
    end_date: datetime

class VoucherCreate(BaseModel):
    code: str
    name: str
    initial_value: float
    expiry_date: Optional[datetime] = None

# --- coupon/voucher validation ---
@router.get("/coupons/validate", response_model=APIResponse[dict])
def validate_coupon(
    code: str,
    cart_value: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    # Find active promotion with coupon code for current user's company
    promo = db.query(Promotion).filter(
        Promotion.coupon_code == code,
        Promotion.company_id == current_user.company_id,
        Promotion.start_date <= now,
        Promotion.end_date >= now
    ).first()
    
    if not promo:
        raise HTTPException(status_code=404, detail="Invalid or expired coupon code")
        
    if float(promo.min_cart_value) > cart_value:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum cart spend of Rs. {promo.min_cart_value} is required for this coupon"
        )
        
    return APIResponse(data={
        "id": promo.id,
        "name": promo.name,
        "type": promo.type, # percentage or flat_discount
        "value": float(promo.value),
        "coupon_code": promo.coupon_code
    })

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

# --- Admin CRUD routes ---
@router.get("/promotions", response_model=APIResponse[List[dict]])
def list_promotions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    promos = db.query(Promotion).filter(Promotion.company_id == current_user.company_id).all()
    res = []
    for p in promos:
        res.append({
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "value": float(p.value),
            "min_cart_value": float(p.min_cart_value),
            "coupon_code": p.coupon_code,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None
        })
    return APIResponse(data=res)

@router.post("/promotions", response_model=APIResponse[dict])
def create_promotion(
    payload: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Promotion).filter(
        Promotion.coupon_code == payload.coupon_code,
        Promotion.company_id == current_user.company_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already registered")
        
    promo = Promotion(
        company_id=current_user.company_id,
        name=payload.name,
        type=payload.type,
        value=payload.value,
        min_cart_value=payload.min_cart_value,
        coupon_code=payload.coupon_code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="active"
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return APIResponse(data={"id": promo.id, "coupon_code": promo.coupon_code})

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

