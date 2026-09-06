import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.rbac import User, Company, Branch
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory, StockTransaction
from app.models.crm import Supplier
from app.models.procurement import GRN, GRNItem

SQLALCHEMY_DATABASE_URL = "sqlite:///file:testdb_proc?mode=memory&cache=shared"

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
    company = Company(name="Test Corp", settings={})
    db_session.add(company)
    db_session.flush()

    branch = Branch(company_id=company.id, name="Main Branch")
    db_session.add(branch)
    db_session.flush()

    user = User(
        company_id=company.id,
        name="Operator 1",
        email="operator@test.com",
        hashed_password=get_password_hash("pass123"),
        is_superadmin=True,
        status="active"
    )
    db_session.add(user)
    db_session.flush()

    # Seed Supplier
    supplier = Supplier(
        company_id=company.id,
        name="Coffee Beans Ltd",
        contact_person="John Beans",
        email="john@coffeebeans.com",
        phone="0777123456",
        ledger_balance=Decimal("0.00")
    )
    db_session.add(supplier)
    db_session.flush()

    # Seed Catalog
    category = Category(company_id=company.id, name="Raw Coffee")
    db_session.add(category)
    db_session.flush()

    product = Product(
        company_id=company.id,
        category_id=category.id,
        name="Ethiopian Beans",
        tax_rate=0.00,
        track_inventory=True,
        reorder_level=5
    )
    db_session.add(product)
    db_session.flush()

    variant = ProductVariant(
        company_id=company.id,
        product_id=product.id,
        name="Light Roast (1kg)",
        sku="BEA-ETH-1KG",
        price=1200.00,
        cost=400.00
    )
    db_session.add(variant)
    db_session.flush()

    # Initial Inventory (10 units, cost=400)
    inventory = Inventory(
        company_id=company.id,
        branch_id=branch.id,
        product_variant_id=variant.id,
        quantity=10,
        avg_cost=Decimal("400.00")
    )
    db_session.add(inventory)
    db_session.flush()

    db_session.commit()

    return {
        "company": company,
        "branch": branch,
        "user": user,
        "supplier": supplier,
        "variant": variant,
        "inventory": inventory
    }

def test_create_supplier_api(client, seed_data):
    # Authenticate
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "operator@test.com", "password": "pass123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add a new supplier
    supplier_res = client.post(
        "/api/v1/crm/suppliers",
        json={
            "company_id": seed_data["company"].id,
            "name": "Milk Farms Inc",
            "contact_person": "Jane Milk",
            "email": "jane@milkfarms.com",
            "phone": "0711122334"
        },
        headers=headers
    )
    assert supplier_res.status_code == 200
    res_data = supplier_res.json()
    assert res_data["success"] is True
    assert res_data["data"]["name"] == "Milk Farms Inc"

def test_record_grn_updates_stock_and_average_cost(client, seed_data):
    # Authenticate
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "operator@test.com", "password": "pass123"}
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Record GRN: Receive 10 units at cost 600
    # Expected inventory after GRN:
    # quantity = 10 (current) + 10 (received) = 20
    # avg_cost = ((10 * 400) + (10 * 600)) / 20 = (4000 + 6000) / 20 = 10000 / 20 = 500
    grn_res = client.post(
        "/api/v1/procurement/grns",
        json={
            "company_id": seed_data["company"].id,
            "branch_id": seed_data["branch"].id,
            "supplier_id": seed_data["supplier"].id,
            "receive_date": "2026-06-03T10:00:00Z",
            "invoice_number": "INV-10023",
            "notes": "Incoming coffee stock",
            "items": [
                {
                    "product_variant_id": seed_data["variant"].id,
                    "quantity_received": 10,
                    "unit_cost": 600.00,
                    "batch_number": "BATCH-009A"
                }
            ]
        },
        headers=headers
    )
    assert grn_res.status_code == 200
    res_data = grn_res.json()
    assert res_data["success"] is True
    assert float(res_data["data"]["total_amount"]) == 6000.00  # 10 * 600

    # Query DB to check updates
    db = TestingSessionLocal()
    inv = db.query(Inventory).filter(Inventory.product_variant_id == seed_data["variant"].id).first()
    assert inv.quantity == 20
    assert float(inv.avg_cost) == 500.00  # Weighted cost calculation check

    # Variant cost should update to latest cost
    var = db.query(ProductVariant).filter(ProductVariant.id == seed_data["variant"].id).first()
    assert float(var.cost) == 600.00

    # Supplier ledger balance should increase by GRN amount
    supp = db.query(Supplier).filter(Supplier.id == seed_data["supplier"].id).first()
    assert float(supp.ledger_balance) == 6000.00

    # Check Stock Transaction log
    txn = db.query(StockTransaction).filter(StockTransaction.product_variant_id == seed_data["variant"].id).first()
    assert txn.quantity == 10
    assert txn.type == "grn"
    assert txn.reference_id == str(res_data["data"]["id"])
    assert txn.reference_type == "grn"

    db.close()
