from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.organization import Company, Branch
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory

def seed_coffee_shop():
    db = SessionLocal()
    try:
        company = db.query(Company).first()
        branch = db.query(Branch).first()
        
        if not company or not branch:
            print("No company or branch found. Run setup-initial-admin first.")
            return

        # 1. Create Categories
        cats_to_create = [
            {"name": "Espresso & Coffee", "description": "Barista-crafted espresso drinks"},
            {"name": "Teas & Matcha", "description": "Premium brewed teas and lattes"},
            {"name": "Bakery & Pastries", "description": "Freshly baked daily pastries"}
        ]
        
        seeded_cats = {}
        for c in cats_to_create:
            cat = db.query(Category).filter(Category.name == c["name"], Category.company_id == company.id).first()
            if not cat:
                cat = Category(
                    company_id=company.id,
                    name=c["name"],
                    description=c["description"],
                    status="active"
                )
                db.add(cat)
                db.flush()
            seeded_cats[c["name"]] = cat

        # 2. Products and Variants setup
        products_to_seed = [
            {
                "category": "Espresso & Coffee",
                "name": "Barista Cappuccino",
                "description": "Espresso topped with thick layer of milk foam",
                "image_url": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?q=80&w=300",
                "tax_rate": Decimal("8.00"),
                "reorder_level": 10,
                "variants": [
                    {"name": "Regular Hot", "price": Decimal("650.00"), "cost": Decimal("180.00"), "sku": "CAP-HOT-REG"},
                    {"name": "Regular Iced", "price": Decimal("720.00"), "cost": Decimal("200.00"), "sku": "CAP-ICE-REG"}
                ]
            },
            {
                "category": "Espresso & Coffee",
                "name": "Classic Caffe Latte",
                "description": "Espresso blended with steamed silky milk",
                "image_url": "https://images.unsplash.com/photo-1541167760496-1628856ab772?q=80&w=300",
                "tax_rate": Decimal("8.00"),
                "reorder_level": 10,
                "variants": [
                    {"name": "Hot / Whole Milk", "price": Decimal("600.00"), "cost": Decimal("150.00"), "sku": "LAT-HOT-WHO"},
                    {"name": "Iced / Oat Milk", "price": Decimal("750.00"), "cost": Decimal("220.00"), "sku": "LAT-ICE-OAT"}
                ]
            },
            {
                "category": "Teas & Matcha",
                "name": "Organic Ceylon Black Tea",
                "description": "Premium loose leaf tea from Nuwara Eliya hills",
                "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=300",
                "tax_rate": Decimal("5.00"),
                "reorder_level": 5,
                "variants": [
                    {"name": "Hot Brew", "price": Decimal("400.00"), "cost": Decimal("80.00"), "sku": "TEA-CEY-HOT"}
                ]
            },
            {
                "category": "Teas & Matcha",
                "name": "Ceremonial Uji Matcha Latte",
                "description": "Stoneground Japanese matcha whisked with milk",
                "image_url": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?q=80&w=300",
                "tax_rate": Decimal("8.00"),
                "reorder_level": 8,
                "variants": [
                    {"name": "Hot Regular", "price": Decimal("850.00"), "cost": Decimal("280.00"), "sku": "MAT-HOT-REG"},
                    {"name": "Iced Regular", "price": Decimal("900.00"), "cost": Decimal("300.00"), "sku": "MAT-ICE-REG"}
                ]
            },
            {
                "category": "Bakery & Pastries",
                "name": "French Chocolate Croissant",
                "description": "Flaky, buttery layers with Belgian chocolate core",
                "image_url": "https://images.unsplash.com/photo-1549778399-f94fd24d68fd?q=80&w=300",
                "tax_rate": Decimal("10.00"),
                "reorder_level": 5,
                "variants": [
                    {"name": "Fresh Baked", "price": Decimal("520.00"), "cost": Decimal("160.00"), "sku": "BAK-CRO-CHOC"}
                ]
            }
        ]

        for p_data in products_to_seed:
            # Check if product exists
            prod = db.query(Product).filter(Product.name == p_data["name"], Product.company_id == company.id).first()
            if not prod:
                prod = Product(
                    company_id=company.id,
                    category_id=seeded_cats[p_data["category"]].id,
                    name=p_data["name"],
                    description=p_data["description"],
                    image_url=p_data["image_url"],
                    tax_rate=p_data["tax_rate"],
                    reorder_level=p_data["reorder_level"],
                    status="active"
                )
                db.add(prod)
                db.flush()

            for v_data in p_data["variants"]:
                variant = db.query(ProductVariant).filter(
                    ProductVariant.sku == v_data["sku"], 
                    ProductVariant.company_id == company.id
                ).first()
                
                if not variant:
                    variant = ProductVariant(
                        company_id=company.id,
                        product_id=prod.id,
                        name=v_data["name"],
                        sku=v_data["sku"],
                        price=v_data["price"],
                        cost=v_data["cost"],
                        attributes={"size": "regular"},
                        status="active"
                    )
                    db.add(variant)
                    db.flush()

                    # Create Inventory starting with 50 units
                    inv = db.query(Inventory).filter(
                        Inventory.branch_id == branch.id,
                        Inventory.product_variant_id == variant.id
                    ).first()
                    
                    if not inv:
                        inv = Inventory(
                            company_id=company.id,
                            branch_id=branch.id,
                            product_variant_id=variant.id,
                            quantity=50,
                            avg_cost=variant.cost,
                            status="active"
                        )
                        db.add(inv)

        db.commit()
        print("Coffee shop / Barista master data seeded successfully with inventory!")
    except Exception as e:
        print(f"Error seeding coffee shop: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_coffee_shop()
