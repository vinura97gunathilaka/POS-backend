from typing import List
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.catalog.product_variant import ProductVariant
from app.models.crm.supplier import Supplier
from app.models.inventory.inventory import Inventory
from app.models.inventory.stock_transaction import StockTransaction
from app.models.procurement.grn import GRN
from app.models.procurement.grn_item import GRNItem
from app.schemas.procurement.grn import GRNCreate, GRNOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/grns", response_model=APIResponse[List[GRNOut]])
def list_grns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(GRN).filter(GRN.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(GRN.company_id == current_user.company_id)
    grns = query.all()
    return APIResponse(data=grns)

@router.get("/grns/{id}", response_model=APIResponse[GRNOut])
def get_grn(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    grn = db.query(GRN).filter(GRN.id == id, GRN.deleted_at == None).first()
    if not grn:
        raise HTTPException(status_code=404, detail="Goods Received Note not found")
    if not current_user.is_superadmin and grn.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return APIResponse(data=grn)

@router.post("/grns", response_model=APIResponse[GRNOut])
def create_grn(
    payload: GRNCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    total_cost_calculated = sum(item.quantity_received * item.unit_cost for item in payload.items)

    grn = GRN(
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        purchase_id=payload.purchase_id,
        supplier_id=payload.supplier_id,
        receive_date=payload.receive_date or datetime.now(timezone.utc),
        total_amount=total_cost_calculated,
        invoice_number=payload.invoice_number,
        notes=payload.notes,
        created_by=current_user.id
    )
    db.add(grn)
    db.flush()

    supplier.ledger_balance += Decimal(str(total_cost_calculated))

    for item in payload.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item.product_variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail=f"Variant ID {item.product_variant_id} not found")

        item_total = item.quantity_received * item.unit_cost

        grn_item = GRNItem(
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            grn_id=grn.id,
            product_variant_id=item.product_variant_id,
            quantity_received=item.quantity_received,
            unit_cost=item.unit_cost,
            total_cost=item_total,
            batch_number=item.batch_number,
            expiry_date=item.expiry_date,
            created_by=current_user.id
        )
        db.add(grn_item)

        inv = db.query(Inventory).filter(
            Inventory.branch_id == payload.branch_id,
            Inventory.product_variant_id == item.product_variant_id
        ).first()

        if not inv:
            inv = Inventory(
                company_id=payload.company_id,
                branch_id=payload.branch_id,
                product_variant_id=item.product_variant_id,
                quantity=item.quantity_received,
                avg_cost=item.unit_cost,
                location_bin=None,
                created_by=current_user.id
            )
            db.add(inv)
            db.flush()
        else:
            curr_qty = Decimal(str(inv.quantity))
            curr_cost = Decimal(str(inv.avg_cost))
            rec_qty = Decimal(str(item.quantity_received))
            rec_cost = Decimal(str(item.unit_cost))
            
            new_qty = curr_qty + rec_qty
            if new_qty > 0:
                new_avg_cost = ((curr_qty * curr_cost) + (rec_qty * rec_cost)) / new_qty
                inv.avg_cost = new_avg_cost
            
            inv.quantity = int(new_qty)
            inv.updated_by = current_user.id

        variant.cost = item.unit_cost

        db.add(StockTransaction(
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            inventory_id=inv.id,
            product_variant_id=item.product_variant_id,
            quantity=item.quantity_received,
            type="grn",
            reference_id=str(grn.id),
            reference_type="grn",
            cost_at_transaction=item.unit_cost,
            created_by=current_user.id
        ))

    db.commit()
    db.refresh(grn)
    return APIResponse(data=grn)
