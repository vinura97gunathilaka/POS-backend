import time
import random
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.organization import Company
from app.models.catalog import ProductVariant
from app.models.crm import Customer, LoyaltyTransaction, LoyaltyRule
from app.models.inventory import Inventory, StockTransaction
from app.models.sales import Sale, SaleItem, Payment, CSATFeedback
from app.schemas.sales import SaleCreate, SaleOut, SaleUpdate, ReceiptDispatchPayload, CSATFeedbackCreate
from app.schemas.response import APIResponse

router = APIRouter()

class KDSBroadcaster:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, company_id: int) -> asyncio.Queue:
        queue = asyncio.Queue()
        if company_id not in self.listeners:
            self.listeners[company_id] = []
        self.listeners[company_id].append(queue)
        return queue

    def unsubscribe(self, company_id: int, queue: asyncio.Queue):
        if company_id in self.listeners:
            if queue in self.listeners[company_id]:
                self.listeners[company_id].remove(queue)
            if not self.listeners[company_id]:
                del self.listeners[company_id]

    def broadcast(self, company_id: int, event_type: str, data: dict = None):
        if company_id in self.listeners:
            for queue in self.listeners[company_id]:
                queue.put_nowait({"event": event_type, "data": data or {}})

kds_broadcaster = KDSBroadcaster()


# --- List & Filter ---
@router.get("/", response_model=APIResponse[List[SaleOut]])
def list_sales(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale).filter(Sale.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Sale.company_id == current_user.company_id)
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
    elif branch_id:
        query = query.filter(Sale.branch_id == branch_id)
    sales = query.all()
    return APIResponse(data=sales)

# --- Hold & Recall ---
@router.get("/held", response_model=APIResponse[List[SaleOut]])
def list_held_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale).filter(Sale.sale_status == "held", Sale.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Sale.company_id == current_user.company_id)
    sales = query.all()
    return APIResponse(data=sales)

# --- Checkout POS ---
@router.post("/checkout", response_model=APIResponse[SaleOut])
def checkout(
    payload: SaleCreate,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate Invoice Number: INV-COMPANYID-BRANCHID-TIMESTAMP
    timestamp = int(time.time())
    rand = random.randint(1000, 9999)
    inv_num = f"INV-{payload.company_id}-{payload.branch_id}-{timestamp}-{rand}"

    # Verify customer and credit balances
    customer = None
    if payload.customer_id:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

    # Total verification (skip if parking the invoice)
    is_held = payload.hold_reference is not None
    total_payment = sum(p.amount for p in payload.payments)
    if not is_held and total_payment < payload.net_amount:
        # Check if customer has credit limit to cover the unpaid balance
        unpaid = payload.net_amount - total_payment
        credit_payment = next((p for p in payload.payments if p.payment_method == "credit"), None)
        
        if credit_payment:
            if not customer:
                raise HTTPException(status_code=400, detail="Customer must be selected for credit purchases")
            if customer.balance + unpaid > customer.credit_limit:
                raise HTTPException(status_code=400, detail="Credit limit exceeded")
            customer.balance += unpaid
        else:
            raise HTTPException(status_code=400, detail="Payment amount does not cover invoice total")


    # Build Sale
    from app.models.organization import Company
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    enable_kds = False
    enable_recipe = False
    if company and company.settings:
        enable_kds = company.settings.get("enable_kds", False)
        enable_recipe = company.settings.get("enable_recipe", False)
    
    prep_status = "pending" if (enable_kds and payload.hold_reference is None) else "none"

    sale = Sale(
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        user_id=current_user.id,
        shift_id=payload.shift_id,
        invoice_number=inv_num,
        sale_date=datetime.utcnow(),
        sub_total=payload.sub_total,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        loyalty_points_redeemed=payload.loyalty_points_redeemed,
        loyalty_discount=payload.loyalty_discount,
        net_amount=payload.net_amount,
        amount_paid=payload.amount_paid,
        change_returned=payload.change_returned,
        payment_status="paid" if total_payment >= payload.net_amount else "partial",
        sale_status="completed" if payload.hold_reference is None else "held",
        preparation_status=prep_status,
        notes=payload.notes,
        hold_reference=payload.hold_reference,
        created_by=current_user.id
    )
    db.add(sale)
    db.flush()

    # Deduct loyalty points if redeemed
    if payload.loyalty_points_redeemed > 0 and customer:
        if customer.points < payload.loyalty_points_redeemed:
            raise HTTPException(status_code=400, detail="Insufficient loyalty points")
        customer.points -= payload.loyalty_points_redeemed
        # Record points deduction
        db.add(LoyaltyTransaction(
            company_id=payload.company_id,
            customer_id=customer.id,
            points=-payload.loyalty_points_redeemed,
            type="redeem",
            reference_id=str(sale.id),
            description=f"Redeemed points for invoice {inv_num}",
            created_by=current_user.id
        ))

    # Process items and deduct stock
    for item in payload.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item.product_variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail=f"Variant ID {item.product_variant_id} not found")

        total_item_amount = (item.quantity * item.unit_price) - item.discount_amount + item.tax_amount

        sale_item = SaleItem(
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            sale_id=sale.id,
            product_variant_id=item.product_variant_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            unit_cost=variant.cost,
            discount_amount=item.discount_amount,
            tax_amount=item.tax_amount,
            total_amount=total_item_amount,
            created_by=current_user.id
        )
        db.add(sale_item)

        # Deduct inventory if product tracks inventory
        if sale.sale_status == "completed":
            if enable_recipe and variant.recipe_components:
                # Deduct all recipe ingredients/components instead of the main variant itself
                for comp in variant.recipe_components:
                    comp_variant = comp.component_variant
                    total_required = comp.quantity * item.quantity
                    
                    inv = db.query(Inventory).filter(
                        Inventory.branch_id == payload.branch_id,
                        Inventory.product_variant_id == comp.component_variant_id
                    ).first()
                    
                    if not inv or inv.quantity < total_required:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient inventory for ingredient '{comp_variant.name}' ({inv.quantity if inv else 0} remaining, needed {total_required})"
                        )
                        
                    inv.quantity -= total_required
                    inv.updated_by = current_user.id
                    
                    # Log Stock Transaction for the component variant
                    db.add(StockTransaction(
                        company_id=payload.company_id,
                        branch_id=payload.branch_id,
                        inventory_id=inv.id,
                        product_variant_id=comp.component_variant_id,
                        quantity=-total_required,
                        type="sale",
                        reference_id=str(sale.id),
                        reference_type="sale",
                        cost_at_transaction=inv.avg_cost,
                        created_by=current_user.id
                    ))
            elif variant.product.track_inventory:
                # Standard inventory item deduction
                inv = db.query(Inventory).filter(
                    Inventory.branch_id == payload.branch_id,
                    Inventory.product_variant_id == item.product_variant_id
                ).first()

                if not inv or inv.quantity < item.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Insufficient inventory for {variant.name} ({inv.quantity if inv else 0} remaining)"
                    )

                inv.quantity -= item.quantity
                inv.updated_by = current_user.id

                # Log Stock Transaction
                db.add(StockTransaction(
                    company_id=payload.company_id,
                    branch_id=payload.branch_id,
                    inventory_id=inv.id,
                    product_variant_id=item.product_variant_id,
                    quantity=-item.quantity,
                    type="sale",
                    reference_id=str(sale.id),
                    reference_type="sale",
                    cost_at_transaction=inv.avg_cost,
                    created_by=current_user.id
                ))


    # Record Payments
    for pay in payload.payments:
        if pay.payment_method == "voucher":
            from app.models.marketing import Voucher
            if not pay.transaction_reference:
                raise HTTPException(status_code=400, detail="Voucher code must be provided in transaction reference")
            voucher = db.query(Voucher).filter(
                Voucher.code == pay.transaction_reference,
                Voucher.company_id == payload.company_id
            ).first()
            if not voucher:
                raise HTTPException(status_code=404, detail=f"Voucher code '{pay.transaction_reference}' not found")
            if voucher.expiry_date and voucher.expiry_date < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Voucher has expired")
            if voucher.balance < pay.amount:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient voucher balance for '{pay.transaction_reference}' (Active Balance: Rs. {voucher.balance})"
                )
            voucher.balance -= pay.amount
            voucher.updated_by = current_user.id

        payment = Payment(
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            sale_id=sale.id,
            amount=pay.amount,
            payment_method=pay.payment_method,
            transaction_reference=pay.transaction_reference,
            bank_account_id=pay.bank_account_id,
            created_by=current_user.id
        )
        db.add(payment)

    # Calculate loyalty points earned (e.g. Rs. 100 spent = 1 point)
    if customer and sale.sale_status == "completed":
        rule = db.query(LoyaltyRule).filter(LoyaltyRule.company_id == payload.company_id, LoyaltyRule.status == "active").first()
        spend_unit = rule.spend_amount if rule else Decimal("100.00")
        earned_points_per_unit = rule.points_earned if rule else 1
        
        # Simple formula
        earned_points = int(sale.net_amount / spend_unit) * earned_points_per_unit
        if earned_points > 0:
            customer.points += earned_points
            db.add(LoyaltyTransaction(
                company_id=payload.company_id,
                customer_id=customer.id,
                points=earned_points,
                type="earn",
                reference_id=str(sale.id),
                description=f"Earned points on invoice {inv_num}",
                created_by=current_user.id
            ))

    # Log Audit Log
    x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request and request.client else None)
    from app.models.logging import AuditLog
    if payload.hold_reference:
        db.add(AuditLog(
            company_id=payload.company_id,
            user_id=current_user.id,
            action="held_sale_park",
            details={
                "hold_reference": payload.hold_reference,
                "net_amount": float(payload.net_amount)
            },
            ip_address=ip_address
        ))
    else:
        db.add(AuditLog(
            company_id=payload.company_id,
            user_id=current_user.id,
            action="sale_checkout",
            details={
                "invoice_number": inv_num,
                "net_amount": float(payload.net_amount),
                "payment_method": payload.payments[0].payment_method if payload.payments else "cash"
            },
            ip_address=ip_address
        ))

    db.commit()
    db.refresh(sale)
    if enable_kds and payload.hold_reference is None:
        kds_broadcaster.broadcast(sale.company_id, "refresh")
    return APIResponse(data=sale)

# --- Cancel Invoice ---
@router.put("/{id}/cancel", response_model=APIResponse[SaleOut])
def cancel_sale(
    id: int,
    payload: SaleUpdate,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify permission: requires manager role or admin
    is_authorized = current_user.is_superadmin or any(role.name in ["Company Admin", "Branch Manager"] for role in current_user.roles)
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invoice cancellation requires manager approval"
        )

    sale = db.query(Sale).filter(Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    
    from app.models.organization import Company
    company = db.query(Company).filter(Company.id == sale.company_id).first()
    enable_recipe = False
    if company and company.settings:
        enable_recipe = company.settings.get("enable_recipe", False)
    
    if sale.sale_status == "cancelled":
        raise HTTPException(status_code=400, detail="Invoice is already cancelled")

    # Reverse stock deduction
    for item in sale.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item.product_variant_id).first()
        if variant:
            if enable_recipe and variant.recipe_components:
                # Reverse for components
                for comp in variant.recipe_components:
                    total_required = comp.quantity * item.quantity
                    inv = db.query(Inventory).filter(
                        Inventory.branch_id == sale.branch_id,
                        Inventory.product_variant_id == comp.component_variant_id
                    ).first()
                    if inv:
                        inv.quantity += total_required
                        # Log reversed transaction
                        db.add(StockTransaction(
                            company_id=sale.company_id,
                            branch_id=sale.branch_id,
                            inventory_id=inv.id,
                            product_variant_id=comp.component_variant_id,
                            quantity=total_required,
                            type="adjustment",
                            reference_id=str(sale.id),
                            reference_type="sale_cancellation",
                            cost_at_transaction=inv.avg_cost,
                            created_by=current_user.id
                        ))
            elif variant.product.track_inventory:
                # Standard inventory reverse
                inv = db.query(Inventory).filter(
                    Inventory.branch_id == sale.branch_id,
                    Inventory.product_variant_id == item.product_variant_id
                ).first()
                if inv:
                    inv.quantity += item.quantity
                    # Log reversed transaction
                    db.add(StockTransaction(
                        company_id=sale.company_id,
                        branch_id=sale.branch_id,
                        inventory_id=inv.id,
                        product_variant_id=item.product_variant_id,
                        quantity=item.quantity,
                        type="adjustment",
                        reference_id=str(sale.id),
                        reference_type="sale_cancellation",
                        cost_at_transaction=inv.avg_cost,
                        created_by=current_user.id
                    ))


    # Reverse customer credit balance if applicable
    if sale.customer_id:
        customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
        if customer:
            # Revert earned loyalty points
            earned_txn = db.query(LoyaltyTransaction).filter(
                LoyaltyTransaction.customer_id == customer.id,
                LoyaltyTransaction.reference_id == str(sale.id),
                LoyaltyTransaction.type == "earn"
            ).first()
            if earned_txn:
                customer.points -= earned_txn.points
                db.delete(earned_txn)

            # Revert redeemed loyalty points
            redeem_txn = db.query(LoyaltyTransaction).filter(
                LoyaltyTransaction.customer_id == customer.id,
                LoyaltyTransaction.reference_id == str(sale.id),
                LoyaltyTransaction.type == "redeem"
            ).first()
            if redeem_txn:
                customer.points += abs(redeem_txn.points)
                db.delete(redeem_txn)

    sale.sale_status = "cancelled"
    sale.payment_status = "refunded"
    sale.notes = f"{sale.notes or ''} [Cancelled: {payload.cancel_reason or 'No reason provided'}]"
    sale.updated_by = current_user.id

    # Log Audit Log
    x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request and request.client else None)
    from app.models.logging import AuditLog
    action_type = "held_sale_recall" if payload.cancel_reason == "Recalled to cart" else "sale_cancellation"
    db.add(AuditLog(
        company_id=sale.company_id,
        user_id=current_user.id,
        action=action_type,
        details={
            "invoice_number": sale.invoice_number,
            "net_amount": float(sale.net_amount),
            "reason": payload.cancel_reason
        },
        ip_address=ip_address
    ))

    db.commit()
    db.refresh(sale)
    kds_broadcaster.broadcast(sale.company_id, "refresh")
    return APIResponse(data=sale)

# --- Public KDS Queue ---
@router.get("/kds/public", response_model=APIResponse[List[dict]])
def list_public_kds_queue(
    company_id: int,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    enable_kds = company.settings.get("enable_kds", False)
    if not enable_kds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order Prep Monitor (KDS Queue) is currently disabled. Please enable it under System Configurations in the dashboard."
        )

    query = db.query(Sale).filter(
        Sale.company_id == company_id,
        Sale.preparation_status.in_(["pending", "preparing", "ready"]),
        Sale.deleted_at == None
    )
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)
        
    sales = query.order_by(Sale.sale_date.asc()).all()
    
    result = []
    for s in sales:
        parts = s.invoice_number.split('-')
        queue_no = parts[-1] if parts else s.invoice_number
        
        result.append({
            "id": s.id,
            "invoice_number": s.invoice_number,
            "queue_number": queue_no,
            "preparation_status": s.preparation_status,
            "sale_date": s.sale_date.isoformat()
        })
        
    return APIResponse(data=result)

# --- KDS Active Queue ---
@router.get("/kds/queue", response_model=APIResponse[List[SaleOut]])
def list_kds_queue(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale).filter(
        Sale.preparation_status.in_(["pending", "preparing", "ready"]),
        Sale.deleted_at == None
    )
    if not current_user.is_superadmin:
        query = query.filter(Sale.company_id == current_user.company_id)
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
    elif branch_id:
        query = query.filter(Sale.branch_id == branch_id)
    
    # Order by checkout timestamp (oldest first)
    sales = query.order_by(Sale.sale_date.asc()).all()
    return APIResponse(data=sales)

# --- Update KDS Prep Status ---
@router.put("/{id}/kds-status", response_model=APIResponse[SaleOut])
def update_kds_status(
    id: int,
    payload: SaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    
    if not current_user.is_superadmin and sale.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if payload.preparation_status not in ["pending", "preparing", "ready", "completed", "none"]:
        raise HTTPException(status_code=400, detail="Invalid preparation status value")
        
    sale.preparation_status = payload.preparation_status
    sale.updated_by = current_user.id
    db.commit()
    db.refresh(sale)
    kds_broadcaster.broadcast(sale.company_id, "refresh")
    return APIResponse(data=sale)

# --- Public Receipt Lookup ---
@router.get("/public/receipt/{invoice_number}", response_model=APIResponse[SaleOut])
def get_public_receipt(
    invoice_number: str,
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(Sale.invoice_number == invoice_number).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice receipt not found")
    return APIResponse(data=sale)

# --- Dispatch Digital Receipt via Email/WhatsApp ---
@router.post("/{id}/dispatch-receipt", response_model=APIResponse[dict])
def dispatch_receipt(
    id: int,
    payload: ReceiptDispatchPayload,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    if not current_user.is_superadmin and sale.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create dispatch logs record
    from app.models.logging import NotificationDispatch
    dispatch_log = NotificationDispatch(
        company_id=sale.company_id,
        branch_id=sale.branch_id,
        sale_id=sale.id,
        type=payload.type,
        recipient=payload.recipient,
        dispatch_status="sent",
        created_by=current_user.id
    )
    db.add(dispatch_log)
    db.commit()

    # Generate simulated notification sending log
    message = f"Invoice {sale.invoice_number} successfully dispatched via {payload.type} to {payload.recipient}"
    print(message)
    return APIResponse(data={"message": message, "status": "sent", "recipient": payload.recipient})


# --- Public KDS Server-Sent Events Route ---
@router.get("/kds/events", response_class=StreamingResponse)
async def kds_events(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    queue = kds_broadcaster.subscribe(company_id)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'event': 'connected'})}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'ping'})}\n\n"
        finally:
            kds_broadcaster.unsubscribe(company_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Public CSAT Feedback Submission ---
@router.post("/public/receipt/{invoice_number}/feedback", response_model=APIResponse[dict])
def submit_receipt_feedback(
    invoice_number: str,
    payload: CSATFeedbackCreate,
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(Sale.invoice_number == invoice_number).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Check if feedback already exists
    existing = db.query(CSATFeedback).filter(CSATFeedback.sale_id == sale.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted for this transaction")
    
    feedback = CSATFeedback(
        company_id=sale.company_id,
        branch_id=sale.branch_id,
        sale_id=sale.id,
        rating=payload.rating,
        feedback_text=payload.feedback_text
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return APIResponse(data={"message": "Feedback submitted successfully", "id": feedback.id})



