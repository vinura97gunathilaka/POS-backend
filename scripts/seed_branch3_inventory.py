import os
import sys

from app.core.database import SessionLocal
from app.models.organization import Company, Branch
from app.models.catalog import ProductVariant
from app.models.inventory import Inventory

db = SessionLocal()

try:
    company = db.query(Company).first()
    branches = db.query(Branch).all()
    variants = db.query(ProductVariant).all()
    
    print("Checking and seeding inventory for all branches...")
    for b in branches:
        for v in variants:
            inv = db.query(Inventory).filter(
                Inventory.branch_id == b.id,
                Inventory.product_variant_id == v.id
            ).first()
            
            if not inv:
                inv = Inventory(
                    company_id=company.id,
                    branch_id=b.id,
                    product_variant_id=v.id,
                    quantity=100,  # Give generous 100 units starting level
                    avg_cost=v.cost,
                    status="active"
                )
                db.add(inv)
                print(f"Seeded 100 units starting inventory for Branch {b.name} (ID {b.id}) - Variant {v.name}")
    db.commit()
    print("Branch inventories checked and updated successfully!")
except Exception as e:
    db.rollback()
    print("Error seeding branch inventory:", e)
finally:
    db.close()
