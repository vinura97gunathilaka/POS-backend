import sys
from scripts.seed_initial_admin import seed_initial_admin
from scripts.seed_coffee_shop import seed_coffee_shop
from scripts.seed_operational import seed_operational
from scripts.seed_marketing import seed_marketing
from scripts.seed_more_data import run_seeding as seed_more_data

def seed_all():
    print("=== Step 1: Seeding Initial Admin, Company & Roles ===")
    seed_initial_admin()

    print("\n=== Step 2: Seeding Coffee Shop Catalog & Products ===")
    seed_coffee_shop()

    print("\n=== Step 3: Seeding Operational Data (Drawers & Accounts) ===")
    seed_operational()

    print("\n=== Step 4: Seeding Marketing (Coupons & Vouchers) ===")
    seed_marketing()

    print("\n=== Step 5: Seeding CRM Customers, Shifts & Sales Transactions ===")
    seed_more_data()

    print("\n=======================================================")
    print("ALL SEEDING COMPLETED SUCCESSFULLY!")
    print("Login with: admin@smartpos.com / admin123")
    print("=======================================================")

if __name__ == "__main__":
    seed_all()
