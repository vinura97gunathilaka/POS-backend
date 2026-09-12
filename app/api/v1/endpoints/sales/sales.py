import time
import random
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.organization.company import Company
from app.models.catalog.product_variant import ProductVariant
from app.models.crm.customer import Customer
from app.models.crm.loyalty_rule import LoyaltyRule
from app.models.crm.loyalty_transaction import LoyaltyTransaction
from app.models.inventory.inventory import Inventory
from app.models.inventory.stock_transaction import StockTransaction
from app.models.sales.sale import Sale
from app.models.sales.sale_item import SaleItem
from app.models.sales.payment import Payment
from app.models.logging.audit_log import AuditLog
from app.models.marketing.voucher import Voucher
from app.schemas.sales.sale import SaleCreate, SaleOut, SaleUpdate
from app.schemas.response import APIResponse
from app.api.v1.endpoints.sales.kds import kds_broadcaster

router = APIRouter()

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

    # Generate Invoice Number: INV-COMPANYID-BRANCHID-TIMESTAMP-RAND
    timestamp = int(time.time())
    rand = random.randint(1000, 9999)
    inv_num = f"INV-{payload.company_id}-{payload.branch_id}-{timestamp}-{rand}"

    # Verify customer and credit balances
    customer = None
    if payload.customer_id:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

    company = db.query(Company).filter(Company.id == payload.company_id).first()
    enable_recipe = False
    enable_kds = False
    if company and company.settings:
        enable_recipe = company.settings.get("enable_recipe", False)
        enable_kds = company.settings.get("enable_kds", False)

    initial_prep_status = "pending" if (enable_kds and not payload.hold_reference) else "none"

    # Create Base Sale Record
    sale = Sale(
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        user_id=current_user.id,
        invoice_number=inv_num,
        sale_date=datetime.now(timezone.utc),
        sub_total=payload.sub_total,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        loyalty_points_redeemed=payload.loyalty_points_redeemed,
        loyalty_discount=payload.loyalty_discount,
        net_amount=payload.net_amount,
        amount_paid=payload.amount_paid,
        change_returned=payload.change_returned,
        notes=payload.notes,
        hold_reference=payload.hold_reference,
        shift_id=payload.shift_id,
        sale_status="held" if payload.hold_reference else "completed",
        payment_status="unpaid" if payload.hold_reference else "paid",
        preparation_status=initial_prep_status,
        created_by=current_user.id
    )
    db.add(sale)
    db.flush()

    # Process Line Items & Deduct Inventory (Only if not held)
    for item in payload.items:
        variant = db.query(ProductVariant).filter(ProductVariant.id == item.product_variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail=f"Product variant ID {item.product_variant_id} not found")

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
            total_amount=(item.unit_price * item.quantity) - item.discount_amount + item.tax_amount,
            created_by=current_user.id
        )
        db.add(sale_item)

        if not payload.hold_reference:
            if enable_recipe and variant.recipe_components:
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

    # Calculate loyalty points earned
    if customer and sale.sale_status == "completed":
        rule = db.query(LoyaltyRule).filter(LoyaltyRule.company_id == payload.company_id, LoyaltyRule.status == "active").first()
        spend_unit = rule.spend_amount if rule else Decimal("100.00")
        earned_points_per_unit = rule.points_earned if rule else 1
        
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
    is_authorized = current_user.is_superadmin or any(role.name in ["Company Admin", "Branch Manager"] for role in current_user.roles)
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invoice cancellation requires manager approval"
        )

    sale = db.query(Sale).filter(Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    
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
                for comp in variant.recipe_components:
                    total_required = comp.quantity * item.quantity
                    inv = db.query(Inventory).filter(
                        Inventory.branch_id == sale.branch_id,
                        Inventory.product_variant_id == comp.component_variant_id
                    ).first()
                    if inv:
                        inv.quantity += total_required
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
                inv = db.query(Inventory).filter(
                    Inventory.branch_id == sale.branch_id,
                    Inventory.product_variant_id == item.product_variant_id
                ).first()
                if inv:
                    inv.quantity += item.quantity
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
            earned_txn = db.query(LoyaltyTransaction).filter(
                LoyaltyTransaction.customer_id == customer.id,
                LoyaltyTransaction.reference_id == str(sale.id),
                LoyaltyTransaction.type == "earn"
            ).first()
            if earned_txn:
                customer.points -= earned_txn.points
                db.delete(earned_txn)

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
