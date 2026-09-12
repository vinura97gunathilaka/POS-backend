from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.organization import Company, Branch
from app.models.auth import User
from app.api.v1.endpoints.users import seed_company_permissions_and_roles
from app.models.finance import CashDrawer, BankAccount
from app.models.crm import LoyaltyRule

def seed_initial_admin():
    db = SessionLocal()
    try:
        user_exists = db.query(User).first()
        if user_exists:
            print("Initial setup already completed. Users exist in database.")
            return

        company = Company(
            name="Smart POS Corp",
            logo_url="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d",
            phone="+94112222222",
            email="info@smartpos.com",
            address="100 Galle Road, Colombo",
            settings={}
        )
        db.add(company)
        db.flush()

        branch = Branch(
            company_id=company.id,
            name="Head Office Branch",
            address="100 Galle Road, Colombo",
            phone="+94112222222",
            email="headoffice@smartpos.com"
        )
        db.add(branch)
        db.flush()

        user = User(
            company_id=company.id,
            name="Super Administrator",
            email="admin@smartpos.com",
            hashed_password=get_password_hash("admin123"),
            phone="+94777123456",
            is_superadmin=True,
            status="active"
        )
        db.add(user)
        db.flush()

        user.branches.append(branch)

        seed_company_permissions_and_roles(db, company.id, user.id)

        drawer = CashDrawer(
            company_id=company.id,
            branch_id=branch.id,
            name="Default Cash Drawer",
            balance=0.00,
            status="active"
        )
        db.add(drawer)

        bank = BankAccount(
            company_id=company.id,
            branch_id=branch.id,
            bank_name="Default Bank",
            account_number="1234567890",
            balance=0.00,
            status="active"
        )
        db.add(bank)

        rule = LoyaltyRule(
            company_id=company.id,
            name="Default Loyalty Rule",
            spend_amount=100.00,
            points_earned=1,
            point_value=1.00,
            status="active"
        )
        db.add(rule)

        db.commit()
        print("Initial admin setup completed successfully!")
        print("Default credentials: admin@smartpos.com / admin123")
    except Exception as e:
        db.rollback()
        print(f"Error during initial setup: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_admin()
