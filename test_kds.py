import sys
from app.core.database import SessionLocal
from app.models.rbac import Company, User, Branch
from app.models.sales import Sale, SaleItem, Payment
from app.models.catalog import ProductVariant
from datetime import datetime, timezone
import time

def run_tests():
    db = SessionLocal()
    print("Starting KDS integration validation tests...")

    # Fetch company and branch
    company = db.query(Company).first()
    if not company:
        print("FAIL: No company found in DB!")
        return False
    
    branch = db.query(Branch).filter(Branch.company_id == company.id).first()
    if not branch:
        print("FAIL: No branch found in DB!")
        return False

    user = db.query(User).filter(User.company_id == company.id).first()
    if not user:
        print("FAIL: No user found in DB!")
        return False

    variant = db.query(ProductVariant).first()
    if not variant:
        print("FAIL: No product variant found in DB to run checkout test!")
        return False

    # TEST 1: Disable KDS and test checkout preparation_status
    print("\n--- Test 1: Checkout with KDS Disabled ---")
    company.settings = {"enable_kds": False}
    db.commit()

    # Create dummy checkout payload
    from app.schemas.sales import SaleCreate, SaleItemCreate, PaymentCreate
    from app.api.v1.endpoints.sales import checkout
    
    payload = SaleCreate(
        company_id=company.id,
        branch_id=branch.id,
        customer_id=None,
        sub_total=variant.price,
        tax_amount=0.0,
        discount_amount=0.0,
        net_amount=variant.price,
        amount_paid=variant.price,
        change_returned=0.0,
        notes="KDS Disabled test checkout",
        shift_id=1,
        items=[
            SaleItemCreate(
                product_variant_id=variant.id,
                quantity=1,
                unit_price=variant.price
            )
        ],
        payments=[
            PaymentCreate(
                amount=variant.price,
                payment_method="cash"
            )
        ]
    )

    # Perform checkout directly calling endpoint logic
    # Mock dependencies
    res = checkout(payload=payload, db=db, current_user=user)
    sale1 = res.data
    print(f"Created Invoice: {sale1.invoice_number}")
    print(f"Sale Status: {sale1.sale_status}")
    print(f"Preparation Status (Expected: 'none'): '{sale1.preparation_status}'")
    
    if sale1.preparation_status != "none":
        print("FAIL: Expected preparation_status to be 'none'")
        return False
    print("PASS: Test 1 Succeeded!")

    # TEST 2: Enable KDS and test checkout preparation_status
    print("\n--- Test 2: Checkout with KDS Enabled ---")
    company.settings = {"enable_kds": True}
    db.commit()

    payload2 = SaleCreate(
        company_id=company.id,
        branch_id=branch.id,
        customer_id=None,
        sub_total=variant.price,
        tax_amount=0.0,
        discount_amount=0.0,
        net_amount=variant.price,
        amount_paid=variant.price,
        change_returned=0.0,
        notes="KDS Enabled test checkout",
        shift_id=1,
        items=[
            SaleItemCreate(
                product_variant_id=variant.id,
                quantity=1,
                unit_price=variant.price
            )
        ],
        payments=[
            PaymentCreate(
                amount=variant.price,
                payment_method="cash"
            )
        ]
    )

    res2 = checkout(payload=payload2, db=db, current_user=user)
    sale2 = res2.data
    print(f"Created Invoice: {sale2.invoice_number}")
    print(f"Preparation Status (Expected: 'pending'): '{sale2.preparation_status}'")

    if sale2.preparation_status != "pending":
        print("FAIL: Expected preparation_status to be 'pending'")
        return False
    print("PASS: Test 2 Succeeded!")

    # TEST 3: Query active KDS queue
    print("\n--- Test 3: Query Active KDS Queue ---")
    from app.api.v1.endpoints.sales import list_kds_queue
    res3 = list_kds_queue(branch_id=branch.id, db=db, current_user=user)
    active_sales = res3.data
    print(f"Active KDS tickets count: {len(active_sales)}")
    found = any(s.id == sale2.id for s in active_sales)
    print(f"New pending sale in queue (Expected: True): {found}")
    
    if not found:
        print("FAIL: Created pending sale was not found in KDS queue!")
        return False
    print("PASS: Test 3 Succeeded!")

    # TEST 4: Transition status: pending -> preparing -> ready -> completed
    print("\n--- Test 4: Transition Status Progression ---")
    from app.api.v1.endpoints.sales import update_kds_status
    from app.schemas.sales import SaleUpdate

    # A. Move to preparing
    res4a = update_kds_status(id=sale2.id, payload=SaleUpdate(preparation_status="preparing"), db=db, current_user=user)
    print(f"Updated status 1 (Expected: 'preparing'): '{res4a.data.preparation_status}'")
    if res4a.data.preparation_status != "preparing":
        print("FAIL: Expected preparing status")
        return False

    # B. Move to ready
    res4b = update_kds_status(id=sale2.id, payload=SaleUpdate(preparation_status="ready"), db=db, current_user=user)
    print(f"Updated status 2 (Expected: 'ready'): '{res4b.data.preparation_status}'")
    if res4b.data.preparation_status != "ready":
        print("FAIL: Expected ready status")
        return False

    # C. Move to completed (clears from KDS)
    res4c = update_kds_status(id=sale2.id, payload=SaleUpdate(preparation_status="completed"), db=db, current_user=user)
    print(f"Updated status 3 (Expected: 'completed'): '{res4c.data.preparation_status}'")
    if res4c.data.preparation_status != "completed":
        print("FAIL: Expected completed status")
        return False

    # D. Confirm cleared from queue
    res4d = list_kds_queue(branch_id=branch.id, db=db, current_user=user)
    found_after_clear = any(s.id == sale2.id for s in res4d.data)
    print(f"Completed sale still in KDS queue (Expected: False): {found_after_clear}")
    if found_after_clear:
        print("FAIL: Completed sale should not be visible in active KDS queue!")
        return False
    
    print("PASS: Test 4 Succeeded!")
    print("\nALL KDS SYSTEM INTEGRATION TESTS PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
