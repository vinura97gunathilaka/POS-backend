import sys
from decimal import Decimal
from app.core.database import SessionLocal
from app.models.rbac import Company, User, Branch
from app.models.sales import Sale, SaleItem, Payment
from app.models.catalog import Product, ProductVariant, ProductVariantComponent
from app.models.inventory import Inventory, StockTransaction

def run_tests():
    db = SessionLocal()
    print("Starting Bill of Materials (BOM) & Recipe-based inventory integration validation tests...")

    # Fetch company, branch and user
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

    # Seed Ingredient 1: Espresso Beans
    beans_prod = db.query(Product).filter(Product.name == "Espresso Beans", Product.company_id == company.id).first()
    if not beans_prod:
        beans_prod = Product(
            company_id=company.id,
            name="Espresso Beans",
            type="product",
            track_inventory=True,
            created_by=user.id
        )
        db.add(beans_prod)
        db.flush()
        
    beans_var = db.query(ProductVariant).filter(ProductVariant.product_id == beans_prod.id).first()
    if not beans_var:
        beans_var = ProductVariant(
            company_id=company.id,
            product_id=beans_prod.id,
            name="Standard",
            sku="BEANS-STD",
            price=Decimal("10.00"),
            cost=Decimal("5.00"),
            created_by=user.id
        )
        db.add(beans_var)
        db.flush()

    # Seed Ingredient 2: Fresh Milk
    milk_prod = db.query(Product).filter(Product.name == "Fresh Milk", Product.company_id == company.id).first()
    if not milk_prod:
        milk_prod = Product(
            company_id=company.id,
            name="Fresh Milk",
            type="product",
            track_inventory=True,
            created_by=user.id
        )
        db.add(milk_prod)
        db.flush()

    milk_var = db.query(ProductVariant).filter(ProductVariant.product_id == milk_prod.id).first()
    if not milk_var:
        milk_var = ProductVariant(
            company_id=company.id,
            product_id=milk_prod.id,
            name="Standard",
            sku="MILK-STD",
            price=Decimal("20.00"),
            cost=Decimal("10.00"),
            created_by=user.id
        )
        db.add(milk_var)
        db.flush()

    # Seed Composite Product: Double Latte
    latte_prod = db.query(Product).filter(Product.name == "Double Latte", Product.company_id == company.id).first()
    if not latte_prod:
        latte_prod = Product(
            company_id=company.id,
            name="Double Latte",
            type="product",
            track_inventory=False, # BOM parent variant doesn't track inventory itself
            created_by=user.id
        )
        db.add(latte_prod)
        db.flush()

    latte_var = db.query(ProductVariant).filter(ProductVariant.product_id == latte_prod.id).first()
    if not latte_var:
        latte_var = ProductVariant(
            company_id=company.id,
            product_id=latte_prod.id,
            name="Standard",
            sku="LATTE-DBL",
            price=Decimal("150.00"),
            cost=Decimal("50.00"),
            created_by=user.id
        )
        db.add(latte_var)
        db.flush()

    # Setup inventory for Espresso Beans & Fresh Milk at this branch
    beans_inv = db.query(Inventory).filter(Inventory.branch_id == branch.id, Inventory.product_variant_id == beans_var.id).first()
    if not beans_inv:
        beans_inv = Inventory(
            company_id=company.id,
            branch_id=branch.id,
            product_variant_id=beans_var.id,
            quantity=100,
            avg_cost=Decimal("5.00"),
            created_by=user.id
        )
        db.add(beans_inv)
    else:
        beans_inv.quantity = 100
        
    milk_inv = db.query(Inventory).filter(Inventory.branch_id == branch.id, Inventory.product_variant_id == milk_var.id).first()
    if not milk_inv:
        milk_inv = Inventory(
            company_id=company.id,
            branch_id=branch.id,
            product_variant_id=milk_var.id,
            quantity=100,
            avg_cost=Decimal("10.00"),
            created_by=user.id
        )
        db.add(milk_inv)
    else:
        milk_inv.quantity = 100

    # Ensure composite latte variant has NO inventory tracking records (or keeps 0)
    latte_inv = db.query(Inventory).filter(Inventory.branch_id == branch.id, Inventory.product_variant_id == latte_var.id).first()
    if not latte_inv:
        latte_inv = Inventory(
            company_id=company.id,
            branch_id=branch.id,
            product_variant_id=latte_var.id,
            quantity=0,
            avg_cost=Decimal("50.00"),
            created_by=user.id
        )
        db.add(latte_inv)
    else:
        latte_inv.quantity = 0

    db.commit()

    # TEST 1: Setup Recipe Components for Double Latte
    print("\n--- Test 1: Setup Recipe Components for Double Latte ---")
    # Delete existing recipe links
    db.query(ProductVariantComponent).filter(ProductVariantComponent.parent_variant_id == latte_var.id).delete()
    
    # Recipe requires: 2 units of Espresso Beans, 3 units of Fresh Milk
    comp1 = ProductVariantComponent(
        company_id=company.id,
        parent_variant_id=latte_var.id,
        component_variant_id=beans_var.id,
        quantity=2,
        created_by=user.id
    )
    comp2 = ProductVariantComponent(
        company_id=company.id,
        parent_variant_id=latte_var.id,
        component_variant_id=milk_var.id,
        quantity=3,
        created_by=user.id
    )
    db.add(comp1)
    db.add(comp2)
    db.commit()
    db.refresh(latte_var)
    print(f"BOM components defined count (Expected: 2): {len(latte_var.recipe_components)}")
    if len(latte_var.recipe_components) != 2:
        print("FAIL: Expected 2 recipe component links.")
        return False
    print("PASS: Test 1 Succeeded!")

    # TEST 2: Checkout with Recipe ENABLED in Company Settings
    print("\n--- Test 2: Checkout with Recipe Toggle Enabled ---")
    company.settings = {"enable_recipe": True, "enable_kds": False}
    db.commit()

    from app.schemas.sales import SaleCreate, SaleItemCreate, PaymentCreate
    from app.api.v1.endpoints.sales import checkout

    payload = SaleCreate(
        company_id=company.id,
        branch_id=branch.id,
        customer_id=None,
        sub_total=latte_var.price * 2,
        tax_amount=0.0,
        discount_amount=0.0,
        net_amount=latte_var.price * 2,
        amount_paid=latte_var.price * 2,
        change_returned=0.0,
        notes="Recipe enabled checkout test",
        shift_id=1,
        items=[
            SaleItemCreate(
                product_variant_id=latte_var.id,
                quantity=2,
                unit_price=latte_var.price
            )
        ],
        payments=[
            PaymentCreate(
                amount=latte_var.price * 2,
                payment_method="cash"
            )
        ]
    )

    res = checkout(payload=payload, db=db, current_user=user)
    sale = res.data
    print(f"Created Sale Invoice: {sale.invoice_number}")

    # Re-fetch inventory quantities
    db.refresh(beans_inv)
    db.refresh(milk_inv)
    db.refresh(latte_inv)

    print(f"Espresso Beans stock level (Expected: 96): {beans_inv.quantity}")
    print(f"Fresh Milk stock level (Expected: 94): {milk_inv.quantity}")
    print(f"Double Latte stock level (Expected: 0): {latte_inv.quantity}")

    if beans_inv.quantity != 96 or milk_inv.quantity != 94 or latte_inv.quantity != 0:
        print("FAIL: Inventory quantities not depleted correctly according to BOM recipe!")
        return False
    print("PASS: Test 2 Succeeded!")

    # TEST 3: Cancel Sale and Revert Recipe Stock Deduction
    print("\n--- Test 3: Cancel Sale and Revert Stock ---")
    from app.api.v1.endpoints.sales import cancel_sale
    from app.schemas.sales import SaleUpdate

    res_cancel = cancel_sale(id=sale.id, payload=SaleUpdate(cancel_reason="Cancel test"), db=db, current_user=user)
    print(f"Sale Status (Expected: 'cancelled'): '{res_cancel.data.sale_status}'")

    db.refresh(beans_inv)
    db.refresh(milk_inv)

    print(f"Espresso Beans stock after cancellation (Expected: 100): {beans_inv.quantity}")
    print(f"Fresh Milk stock after cancellation (Expected: 100): {milk_inv.quantity}")

    if beans_inv.quantity != 100 or milk_inv.quantity != 100:
        print("FAIL: Reversal did not restore component ingredients inventory levels!")
        return False
    print("PASS: Test 3 Succeeded!")

    # TEST 4: Checkout with Recipe DISABLED in Company Settings
    print("\n--- Test 4: Checkout with Recipe Toggle Disabled ---")
    company.settings = {"enable_recipe": False, "enable_kds": False}
    db.commit()

    # Re-checkout latte
    payload2 = SaleCreate(
        company_id=company.id,
        branch_id=branch.id,
        customer_id=None,
        sub_total=latte_var.price * 2,
        tax_amount=0.0,
        discount_amount=0.0,
        net_amount=latte_var.price * 2,
        amount_paid=latte_var.price * 2,
        change_returned=0.0,
        notes="Recipe disabled checkout test",
        shift_id=1,
        items=[
            SaleItemCreate(
                product_variant_id=latte_var.id,
                quantity=2,
                unit_price=latte_var.price
            )
        ],
        payments=[
            PaymentCreate(
                amount=latte_var.price * 2,
                payment_method="cash"
            )
        ]
    )

    res2 = checkout(payload=payload2, db=db, current_user=user)
    sale2 = res2.data
    print(f"Created Sale Invoice: {sale2.invoice_number}")

    db.refresh(beans_inv)
    db.refresh(milk_inv)
    db.refresh(latte_inv)

    print(f"Espresso Beans stock level (Expected: 100): {beans_inv.quantity}")
    print(f"Fresh Milk stock level (Expected: 100): {milk_inv.quantity}")

    if beans_inv.quantity != 100 or milk_inv.quantity != 100:
        print("FAIL: Ingredients were depleted even though recipes were disabled globally!")
        return False
    print("PASS: Test 4 Succeeded!")

    print("\nALL BILL OF MATERIALS & RECIPE INTEGRATION TESTS PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
