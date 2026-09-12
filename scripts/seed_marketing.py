from datetime import datetime, timedelta
from decimal import Decimal
from app.core.database import SessionLocal
from app.models.rbac import Company
from app.models.marketing import Promotion, Voucher

def seed_marketing():
    seed_marketing_data()

def seed_marketing_data():
    db = SessionLocal()
    try:
        company = db.query(Company).first()
        if not company:
            print("No company found. Please run initial setup first.")
            return

        print(f"Seeding marketing data for company: {company.name} (ID: {company.id})")
        
        now = datetime.utcnow()
        future = now + timedelta(days=365)
        past = now - timedelta(days=1)

        # 1. Seed Promotions/Coupons
        coupons = [
            {
                "name": "10% Welcome Discount",
                "type": "percentage",
                "value": Decimal("10.00"),
                "min_cart_value": Decimal("500.00"),
                "coupon_code": "WELCOME10",
                "start_date": past,
                "end_date": future
            },
            {
                "name": "Rs. 200 Flat Discount",
                "type": "flat_discount",
                "value": Decimal("200.00"),
                "min_cart_value": Decimal("1000.00"),
                "coupon_code": "FLAT200",
                "start_date": past,
                "end_date": future
            }
        ]

        for c_data in coupons:
            promo = db.query(Promotion).filter(
                Promotion.coupon_code == c_data["coupon_code"],
                Promotion.company_id == company.id
            ).first()
            
            if not promo:
                promo = Promotion(
                    company_id=company.id,
                    name=c_data["name"],
                    type=c_data["type"],
                    value=c_data["value"],
                    min_cart_value=c_data["min_cart_value"],
                    coupon_code=c_data["coupon_code"],
                    start_date=c_data["start_date"],
                    end_date=c_data["end_date"],
                    status="active"
                )
                db.add(promo)
                print(f"Created Coupon: {c_data['coupon_code']}")

        # 2. Seed Vouchers
        vouchers = [
            {
                "code": "GIFT500",
                "name": "Rs. 500 Gift Voucher",
                "initial_value": Decimal("500.00"),
                "balance": Decimal("500.00"),
                "expiry_date": future
            },
            {
                "code": "GIFT1000",
                "name": "Rs. 1000 Gift Voucher",
                "initial_value": Decimal("1000.00"),
                "balance": Decimal("1000.00"),
                "expiry_date": future
            }
        ]

        for v_data in vouchers:
            vouch = db.query(Voucher).filter(
                Voucher.code == v_data["code"],
                Voucher.company_id == company.id
            ).first()
            
            if not vouch:
                vouch = Voucher(
                    company_id=company.id,
                    code=v_data["code"],
                    name=v_data["name"],
                    initial_value=v_data["initial_value"],
                    balance=v_data["balance"],
                    expiry_date=v_data["expiry_date"],
                    status="active"
                )
                db.add(vouch)
                print(f"Created Gift Voucher: {v_data['code']}")

        db.commit()
        print("Marketing seed data populated successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_marketing_data()
