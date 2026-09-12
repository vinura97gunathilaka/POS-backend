from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.catalog.product_variant import ProductVariant
from app.models.inventory.inventory import Inventory
from app.models.inventory.stock_transaction import StockTransaction
from app.schemas.inventory.inventory import InventoryOut
from app.schemas.inventory.stock_transaction import StockAdjustmentPayload
from app.schemas.response import APIResponse

router = APIRouter()

# --- Inventory Query ---
@router.get("/", response_model=APIResponse[List[InventoryOut]])
def list_inventories(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Inventory).filter(Inventory.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Inventory.company_id == current_user.company_id)
        if branch_id:
            query = query.filter(Inventory.branch_id == branch_id)
    elif branch_id:
        query = query.filter(Inventory.branch_id == branch_id)
    
    inventories = query.all()
    return APIResponse(data=inventories)

# --- Manual Stock Adjustment ---
@router.post("/adjust", response_model=APIResponse[InventoryOut])
def adjust_stock(
    payload: StockAdjustmentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    variant = db.query(ProductVariant).filter(ProductVariant.id == payload.product_variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")

    inv = db.query(Inventory).filter(
        Inventory.branch_id == payload.branch_id,
        Inventory.product_variant_id == payload.product_variant_id
    ).first()

    if not inv:
        inv = Inventory(
            company_id=variant.company_id,
            branch_id=payload.branch_id,
            product_variant_id=payload.product_variant_id,
            quantity=0,
            avg_cost=variant.cost,
            created_by=current_user.id
        )
        db.add(inv)
        db.flush()

    inv.quantity += payload.quantity
    if inv.quantity < 0:
        raise HTTPException(status_code=400, detail="Inventory quantity cannot drop below zero")

    inv.updated_by = current_user.id

    txn = StockTransaction(
        company_id=variant.company_id,
        branch_id=payload.branch_id,
        inventory_id=inv.id,
        product_variant_id=payload.product_variant_id,
        quantity=payload.quantity,
        type=payload.type,
        reference_type="adjustment",
        cost_at_transaction=variant.cost,
        created_by=current_user.id
    )
    db.add(txn)
    db.commit()
    db.refresh(inv)

    return APIResponse(data=inv)
