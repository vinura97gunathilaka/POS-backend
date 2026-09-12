from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.rbac import Company, Branch
from app.models.finance import CashDrawer, BankAccount
from app.models.crm import LoyaltyRule

def seed_operational():
    seed()

def seed():
    db = SessionLocal()
    try:
        # Get first company and branch
        company = db.query(Company).first()
        branch = db.query(Branch).first()
        
        if not company or not branch:
            print("No company or branch found. Please run initial admin setup first.")
            return

        # Check if cash drawer exists
        drawer = db.query(CashDrawer).filter(CashDrawer.company_id == company.id).first()
        if not drawer:
            drawer = CashDrawer(
                company_id=company.id,
                branch_id=branch.id,
                name="Default Cash Drawer",
                balance=0.00,
                status="active"
            )
            db.add(drawer)
            print("Seeded Cash Drawer.")

        # Check if bank account exists
        bank = db.query(BankAccount).filter(BankAccount.company_id == company.id).first()
        if not bank:
            bank = BankAccount(
                company_id=company.id,
                branch_id=branch.id,
                bank_name="Default Bank",
                account_number="1234567890",
                balance=0.00,
                status="active"
            )
            db.add(bank)
            print("Seeded Bank Account.")

        # Check if loyalty rule exists
        rule = db.query(LoyaltyRule).filter(LoyaltyRule.company_id == company.id).first()
        if not rule:
            rule = LoyaltyRule(
                company_id=company.id,
                name="Default Loyalty Rule",
                spend_amount=100.00,
                points_earned=1,
                point_value=1.00,
                status="active"
            )
            db.add(rule)
            print("Seeded Loyalty Rule.")

        db.commit()
        print("Operational seeding completed successfully.")
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
