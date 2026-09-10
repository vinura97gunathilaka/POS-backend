from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.organization import Branch
from app.models.catalog import ProductVariant
from app.models.inventory import Inventory, StockTransaction, StockTransfer, StockTransferItem
from app.schemas.inventory import (
    InventoryOut, StockTransactionOut,
    StockTransferCreate, StockTransferUpdate, StockTransferOut,
    StockAdjustmentPayload
)
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
    # Verify user access to branch
    if not current_user.is_superadmin and current_user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get variant
    variant = db.query(ProductVariant).filter(ProductVariant.id == payload.product_variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")

    # Find or create inventory item
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

    # Update qty
    inv.quantity += payload.quantity
    if inv.quantity < 0:
        raise HTTPException(status_code=400, detail="Inventory quantity cannot drop below zero")

    inv.updated_by = current_user.id

    # Create Transaction Entry
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

# --- Cross-Branch Transfers ---
@router.get("/transfers", response_model=APIResponse[List[StockTransferOut]])
def list_transfers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(StockTransfer)
    if not current_user.is_superadmin:
        query = query.filter(StockTransfer.company_id == current_user.company_id)
    transfers = query.all()
    return APIResponse(data=transfers)

@router.post("/transfers", response_model=APIResponse[StockTransferOut])
def initiate_transfer(
    payload: StockTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    transfer = StockTransfer(
        company_id=payload.company_id,
        from_branch_id=payload.from_branch_id,
        to_branch_id=payload.to_branch_id,
        transfer_date=payload.transfer_date,
        total_items=len(payload.items),
        status="requested",
        created_by=current_user.id
    )
    db.add(transfer)
    db.flush()

    for item in payload.items:
        # Check source inventory
        src_inv = db.query(Inventory).filter(
            Inventory.branch_id == payload.from_branch_id,
            Inventory.product_variant_id == item.product_variant_id
        ).first()

        if not src_inv or src_inv.quantity < item.quantity_transferred:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient inventory for variant ID {item.product_variant_id} in source branch"
            )

        transfer_item = StockTransferItem(
            company_id=payload.company_id,
            stock_transfer_id=transfer.id,
            product_variant_id=item.product_variant_id,
            quantity_transferred=item.quantity_transferred,
            created_by=current_user.id
        )
        db.add(transfer_item)

    db.commit()
    db.refresh(transfer)
    return APIResponse(data=transfer)

@router.put("/transfers/{id}", response_model=APIResponse[StockTransferOut])
def update_transfer_status(
    id: int,
    payload: StockTransferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transfer = db.query(StockTransfer).filter(StockTransfer.id == id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Stock transfer not found")
    
    if not current_user.is_superadmin and transfer.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    old_status = transfer.status
    new_status = payload.status or transfer.status

    if old_status == "received" or old_status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot alter completed or cancelled transfers")

    # Transit status: Deduct from source branch
    if new_status == "transit" and old_status == "requested":
        for item in transfer.items:
            src_inv = db.query(Inventory).filter(
                Inventory.branch_id == transfer.from_branch_id,
                Inventory.product_variant_id == item.product_variant_id
            ).first()

            if not src_inv or src_inv.quantity < item.quantity_transferred:
                raise HTTPException(status_code=400, detail="Insufficient quantity for dispatch")

            src_inv.quantity -= item.quantity_transferred
            src_inv.updated_by = current_user.id

            txn = StockTransaction(
                company_id=transfer.company_id,
                branch_id=transfer.from_branch_id,
                inventory_id=src_inv.id,
                product_variant_id=item.product_variant_id,
                quantity=-item.quantity_transferred,
                type="transfer_out",
                reference_id=str(transfer.id),
                reference_type="transfer",
                cost_at_transaction=src_inv.avg_cost,
                created_by=current_user.id
            )
            db.add(txn)

    # Received status: Add to destination branch
    elif new_status == "received" and old_status == "transit":
        # Create dictionary mapping variant -> received qty for ease
        received_map = {}
        if payload.items_received:
            for item in payload.items_received:
                received_map[item["product_variant_id"]] = item["quantity_received"]

        for item in transfer.items:
            qty_rec = received_map.get(item.product_variant_id, item.quantity_transferred)
            item.quantity_received = qty_rec
            item.updated_by = current_user.id

            # Destination Inventory update
            dest_inv = db.query(Inventory).filter(
                Inventory.branch_id == transfer.to_branch_id,
                Inventory.product_variant_id == item.product_variant_id
            ).first()

            # Retrieve variant cost for initializing
            variant = db.query(ProductVariant).filter(ProductVariant.id == item.product_variant_id).first()

            if not dest_inv:
                dest_inv = Inventory(
                    company_id=transfer.company_id,
                    branch_id=transfer.to_branch_id,
                    product_variant_id=item.product_variant_id,
                    quantity=0,
                    avg_cost=variant.cost if variant else 0.00,
                    created_by=current_user.id
                )
                db.add(dest_inv)
                db.flush()

            dest_inv.quantity += qty_rec
            dest_inv.updated_by = current_user.id

            txn = StockTransaction(
                company_id=transfer.company_id,
                branch_id=transfer.to_branch_id,
                inventory_id=dest_inv.id,
                product_variant_id=item.product_variant_id,
                quantity=qty_rec,
                type="transfer_in",
                reference_id=str(transfer.id),
                reference_type="transfer",
                cost_at_transaction=dest_inv.avg_cost,
                created_by=current_user.id
            )
            db.add(txn)

    transfer.status = new_status
    if payload.notes:
        transfer.notes = payload.notes
    transfer.updated_by = current_user.id

    db.commit()
    db.refresh(transfer)
    return APIResponse(data=transfer)

