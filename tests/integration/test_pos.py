import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.core.database import get_db

from app.core.security import get_password_hash
from app.models.auth import User
from app.models.organization import Company, Branch
from app.models.finance import CashDrawer, Shift
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory
from app.models.sales import Sale

# Use SQLite memory database with shared cache for multi-connection FastAPI client tests
SQLALCHEMY_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "uri": True}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def seed_data(db_session):
    # Seed company
    company = Company(name="Test Company", settings={})
    db_session.add(company)
    db_session.flush()

    # Seed branch
    branch = Branch(company_id=company.id, name="Test Branch")
    db_session.add(branch)
    db_session.flush()

    # Seed user
    user = User(
        company_id=company.id,
        name="Test Operator",
        email="test@smartpos.com",
        hashed_password=get_password_hash("password123"),
        is_superadmin=True,
        status="active"
    )
    db_session.add(user)
    db_session.flush()

    # Seed Cash Drawer
    drawer = CashDrawer(
        company_id=company.id,
        branch_id=branch.id,
        name="Cash Drawer 1",
        balance=0.00
    )
    db_session.add(drawer)
    db_session.flush()

    # Seed Catalog
    category = Category(company_id=company.id, name="Beverages")
    db_session.add(category)
    db_session.flush()

    product = Product(
        company_id=company.id,
        category_id=category.id,
        name="Cappuccino",
        tax_rate=8.00,
        track_inventory=True,
        reorder_level=5
    )
    db_session.add(product)
    db_session.flush()

    variant = ProductVariant(
        company_id=company.id,
        product_id=product.id,
        name="Hot / Large",
        sku="CAP-HOT-LRG",
        price=600.00,
        cost=150.00
    )
    db_session.add(variant)
    db_session.flush()

    # Seed Inventory
    inventory = Inventory(
        company_id=company.id,
        branch_id=branch.id,
        product_variant_id=variant.id,
        quantity=20,
        avg_cost=150.00
    )
    db_session.add(inventory)
    db_session.flush()

    db_session.commit()

    return {
        "company": company,
        "branch": branch,
        "user": user,
        "drawer": drawer,
        "category": category,
        "product": product,
        "variant": variant,
        "inventory": inventory
    }

# 1. Test Authentication login flow
def test_login(client, seed_data):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@smartpos.com", "password": "password123"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "access_token" in res_data["data"]

# 2. Test active shift opening & cash reconciliation
def test_shift_lifecycle(client, seed_data):
    # Obtain auth token
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@smartpos.com", "password": "password123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Open Shift
    open_res = client.post(
        "/api/v1/finance/shifts",
        json={
            "company_id": seed_data["company"].id,
            "branch_id": seed_data["branch"].id,
            "cash_drawer_id": seed_data["drawer"].id,
            "opening_balance": 5000.00,
            "notes": "Test Open Shift"
        },
        headers=headers
    )
    assert open_res.status_code == 200
    shift_data = open_res.json()["data"]
    assert shift_data["status"] == "open"
    assert float(shift_data["opening_balance"]) == 5000.00

    # Close Shift
    close_res = client.put(
        f"/api/v1/finance/shifts/{shift_data['id']}/close",
        json={
            "actual_cash": 5000.00,
            "notes": "Close Drawer match"
        },
        headers=headers
    )
    assert close_res.status_code == 200
    closed_data = close_res.json()["data"]
    assert closed_data["status"] == "closed"
    assert float(closed_data["variance"]) == 0.00

# 3. Test POS billing checkout, stock deduction, and sales tracking
def test_pos_checkout(client, seed_data):
    # Obtain token
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@smartpos.com", "password": "password123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Open Shift first
    open_res = client.post(
        "/api/v1/finance/shifts",
        json={
            "company_id": seed_data["company"].id,
            "branch_id": seed_data["branch"].id,
            "cash_drawer_id": seed_data["drawer"].id,
            "opening_balance": 5000.00
        },
        headers=headers
    )
    shift_id = open_res.json()["data"]["id"]

    # Checkout sale
    checkout_res = client.post(
        "/api/v1/sales/checkout",
        json={
            "company_id": seed_data["company"].id,
            "branch_id": seed_data["branch"].id,
            "sub_total": 600.00,
            "tax_amount": 48.00,
            "discount_amount": 0.00,
            "net_amount": 648.00,
            "amount_paid": 650.00,
            "change_returned": 2.00,
            "shift_id": shift_id,
            "items": [
                {
                    "product_variant_id": seed_data["variant"].id,
                    "quantity": 1,
                    "unit_price": 600.00
                }
            ],
            "payments": [
                {
                    "amount": 650.00,
                    "payment_method": "cash"
                }
            ]
        },
        headers=headers
    )
    assert checkout_res.status_code == 200
    sale_data = checkout_res.json()["data"]
    assert sale_data["payment_status"] == "paid"

    # Verify inventory is deducted
    db = TestingSessionLocal()
    inv = db.query(Inventory).filter(Inventory.product_variant_id == seed_data["variant"].id).first()
    assert inv.quantity == 19 # 20 - 1 = 19
    db.close()

# 4. Test POS Hold / Recall billing
def test_hold_recall_bill(client, seed_data):
    # Obtain token
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@smartpos.com", "password": "password123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Open Shift first
    open_res = client.post(
        "/api/v1/finance/shifts",
        json={
            "company_id": seed_data["company"].id,
            "branch_id": seed_data["branch"].id,
            "cash_drawer_id": seed_data["drawer"].id,
            "opening_balance": 5000.00
        },
        headers=headers
    )
    shift_id = open_res.json()["data"]["id"]

    # Park / Hold bill (should bypass payment verification)
    hold_res = client.post(
        "/api/v1/sales/checkout",
        json={
            "company_id": seed_data["company"].id,
            "branch_id": seed_data["branch"].id,
            "sub_total": 600.00,
            "tax_amount": 48.00,
            "discount_amount": 0.00,
            "net_amount": 648.00,
            "amount_paid": 0.00,
            "change_returned": 0.00,
            "hold_reference": "Ref-9999",
            "shift_id": shift_id,
            "items": [
                {
                    "product_variant_id": seed_data["variant"].id,
                    "quantity": 1,
                    "unit_price": 600.00
                }
            ],
            "payments": []
        },
        headers=headers
    )
    assert hold_res.status_code == 200
    hold_data = hold_res.json()["data"]
    assert hold_data["sale_status"] == "held"

# 5. Test manual stock adjustments
def test_stock_adjustment(client, seed_data):
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@smartpos.com", "password": "password123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Adjust stock (add 15 units)
    adjust_res = client.post(
        "/api/v1/inventory/adjust",
        json={
            "branch_id": seed_data["branch"].id,
            "product_variant_id": seed_data["variant"].id,
            "quantity": 15,
            "type": "adjustment"
        },
        headers=headers
    )
    assert adjust_res.status_code == 200
    assert adjust_res.json()["data"]["quantity"] == 35 # 20 + 15 = 35

