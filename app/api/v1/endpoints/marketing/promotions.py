from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.marketing.promotion import Promotion
from app.schemas.marketing.promotion import PromotionCreate
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/coupons/validate", response_model=APIResponse[dict])
def validate_coupon(
    code: str,
    cart_value: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
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
        "type": promo.type,
        "value": float(promo.value),
        "coupon_code": promo.coupon_code
    })

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
