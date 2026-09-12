from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.procurement.purchase import Purchase
from app.models.procurement.purchase_item import PurchaseItem
from app.schemas.procurement.purchase import PurchaseCreate, PurchaseOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/purchases", response_model=APIResponse[List[PurchaseOut]])
def list_purchases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Purchase).filter(Purchase.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Purchase.company_id == current_user.company_id)
    purchases = query.all()
    return APIResponse(data=purchases)

@router.get("/purchases/{id}", response_model=APIResponse[PurchaseOut])
def get_purchase(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchase = db.query(Purchase).filter(Purchase.id == id, Purchase.deleted_at == None).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if not current_user.is_superadmin and purchase.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return APIResponse(data=purchase)

@router.post("/purchases", response_model=APIResponse[PurchaseOut])
def create_purchase(
    payload: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    total_cost = sum(item.quantity * item.unit_cost for item in payload.items)
    net_amount = total_cost + payload.tax_amount - payload.discount_amount

    purchase = Purchase(
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        supplier_id=payload.supplier_id,
        order_date=payload.order_date,
        expected_delivery=payload.expected_delivery,
        total_amount=total_cost,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        net_amount=net_amount,
        notes=payload.notes,
        created_by=current_user.id
    )
    db.add(purchase)
    db.flush()

    for item in payload.items:
        pi = PurchaseItem(
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            purchase_id=purchase.id,
            product_variant_id=item.product_variant_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            total_cost=item.quantity * item.unit_cost,
            created_by=current_user.id
        )
        db.add(pi)

    db.commit()
    db.refresh(purchase)
    return APIResponse(data=purchase)
