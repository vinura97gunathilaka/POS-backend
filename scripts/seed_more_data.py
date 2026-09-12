import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Add backend directory to Python path
from app.core.database import SessionLocal
from app.models.organization import Company, Branch
from app.models.auth import User
from app.models.catalog import ProductVariant
from app.models.crm import Customer, LoyaltyTransaction, LoyaltyRule
from app.models.sales import Sale, SaleItem, Payment
from app.models.finance import Shift
from app.models.logging import AuditLog, NotificationDispatch

db = SessionLocal()

def run_seeding():
    try:
        company = db.query(Company).first()
        branches = db.query(Branch).all()
        users = db.query(User).all()
        variants = db.query(ProductVariant).all()

        if not company or not branches or not users or not variants:
            print("Missing core data (company, branches, users, or product variants). Run initial seeds first.")
            return

        print("Clearing old transactional, customer, and log data...")
        db.query(NotificationDispatch).delete()
        db.query(AuditLog).delete()
        db.query(LoyaltyTransaction).delete()
        db.query(Payment).delete()
        db.query(SaleItem).delete()
        db.query(Sale).delete()
        db.query(Shift).delete()
        db.query(Customer).delete()
        db.commit()

        print("Seeding Customers (CRM)...")
        customer_names = [
            ("Amal Silva", "amal@silva.com", "+94771234567"),
            ("Nimal Perera", "nimal@perera.com", "+94777654321"),
            ("Kamal Fernando", "kamal@fernando.com", "+94711122334"),
            ("Dilini Cooray", "dilini@cooray.com", "+94722233445"),
            ("Ruwan Jayasinghe", "ruwan@jayasinghe.com", "+94755566778"),
            ("Priyantha Bandara", "priyantha@bandara.com", "+94778899001"),
            ("Sanduni Peiris", "sanduni@peiris.com", "+94773344556"),
            ("Kavinda Rajapaksha", "kavinda@rajapaksha.com", "+94712233445"),
            ("Thisara Perera", "thisara@perera.com", "+94774455667"),
            ("Chaturika Siriwardene", "chaturika@siriwardene.com", "+94722255667"),
            ("Dilan Gunawardena", "dilan@gunawardena.com", "+94766677889"),
            ("Nisansala Kumari", "nisansala@kumari.com", "+94779900112"),
            ("Ishara Madushanka", "ishara@madushanka.com", "+94771122338"),
            ("Hansani Herath", "hansani@herath.com", "+94755588990"),
            ("Kasun Wijesinghe", "kasun@wijesinghe.com", "+94715566778")
        ]

        customers = []
        for name, email, phone in customer_names:
            c = Customer(
                company_id=company.id,
                name=name,
                email=email,
                phone=phone,
                points=random.randint(10, 600),
                credit_limit=Decimal("50000.00"),
                balance=Decimal("0.00")
            )
            db.add(c)
            db.flush()
            customers.append(c)

        print(f"Seeded {len(customers)} customers successfully.")

        # Ensure a default loyalty rule exists
        rule = db.query(LoyaltyRule).filter(LoyaltyRule.company_id == company.id).first()
        if not rule:
            rule = LoyaltyRule(
                company_id=company.id,
                name="Default Rule",
                spend_amount=Decimal("100.00"),
                points_earned=1,
                point_value=Decimal("1.00")
            )
            db.add(rule)
            db.flush()

        print("Seeding Cashier Shifts...")
        shifts = []
        now = datetime.utcnow()
        # Create shifts over the last 30 days
        for day in range(30, 0, -1):
            shift_date = now - timedelta(days=day)
            
            # Seed 1 shift per day for random cashier
            cashier = random.choice(users)
            branch = random.choice(branches)
            
            # Opening balance
            open_bal = Decimal("5000.00")
            
            # Expected and actual cash (random variance)
            expected = open_bal + Decimal(str(random.randint(2000, 15000)))
            variance = Decimal(str(random.choice([-150.0, -50.0, 0.0, 0.0, 0.0, 100.0, 200.0])))
            actual = expected + variance
            
            s = Shift(
                company_id=company.id,
                branch_id=branch.id,
                user_id=cashier.id,
                cash_drawer_id=1,
                status="closed",
                open_time=shift_date.replace(hour=8, minute=0, second=0),
                close_time=shift_date.replace(hour=17, minute=0, second=0),
                opening_balance=open_bal,
                expected_cash=expected,
                actual_cash=actual,
                variance=variance,
                notes=f"Shift closed on day {day} with variance {variance}",
                created_at=shift_date.replace(hour=8, minute=0, second=0),
                updated_at=shift_date.replace(hour=17, minute=0, second=0)
            )
            db.add(s)
            db.flush()
            shifts.append(s)

        print(f"Seeded {len(shifts)} shifts successfully.")

        print("Seeding Sales Transactions and Payments...")
        sales_count = 0
        payment_methods = ["CASH", "CARD", "QR_PAYMENT", "CASH", "CARD"] # Favor cash and card

        # Generate 1 to 4 sales per shift
        for shift in shifts:
            sales_for_shift = random.randint(1, 4)
            for s_idx in range(sales_for_shift):
                sales_count += 1
                
                # Transaction date/time within the shift bounds
                s_hour = random.randint(8, 16)
                s_minute = random.randint(0, 59)
                sale_date = shift.created_at.replace(hour=s_hour, minute=s_minute)
                
                # Customer (30% chance walk-in, 70% loyalty customer)
                customer = None
                if random.random() < 0.7:
                    customer = random.choice(customers)

                # Invoice Number
                invoice_no = f"INV-{sale_date.strftime('%Y%m%d')}-{sales_count:04d}"

                # Create Sale record
                sale = Sale(
                    company_id=company.id,
                    branch_id=shift.branch_id,
                    customer_id=customer.id if customer else None,
                    user_id=shift.user_id,
                    shift_id=shift.id,
                    invoice_number=invoice_no,
                    sale_date=sale_date,
                    payment_status="paid",
                    sale_status="completed",
                    preparation_status="none",
                    notes=f"Simulated transaction {sales_count}"
                )
                db.add(sale)
                db.flush()

                # Add 1 to 5 random items to the sale
                sub_total = Decimal("0.00")
                tax_total = Decimal("0.00")
                discount_total = Decimal("0.00")
                
                sale_variants = random.sample(variants, min(len(variants), random.randint(1, 4)))
                for v in sale_variants:
                    qty = random.randint(1, 3)
                    item_price = v.price
                    item_cost = v.cost
                    item_tax_rate = Decimal("8.00") # Assume 8% default tax rate
                    
                    item_sub = item_price * qty
                    item_tax = (item_sub * (item_tax_rate / 100)).quantize(Decimal("0.01"))
                    item_discount = Decimal("0.00")
                    
                    # 10% chance of a discount
                    if random.random() < 0.15:
                        item_discount = (item_sub * Decimal("0.10")).quantize(Decimal("0.01"))
                        
                    item_net = item_sub + item_tax - item_discount
                    
                    sale_item = SaleItem(
                        company_id=company.id,
                        branch_id=shift.branch_id,
                        sale_id=sale.id,
                        product_variant_id=v.id,
                        quantity=qty,
                        unit_price=item_price,
                        unit_cost=item_cost,
                        discount_amount=item_discount,
                        tax_amount=item_tax,
                        total_amount=item_net
                    )
                    db.add(sale_item)
                    
                    sub_total += item_sub
                    tax_total += item_tax
                    discount_total += item_discount

                net_total = sub_total + tax_total - discount_total
                
                # Check for loyalty point redemption (if customer has points, 10% chance)
                loyalty_discount = Decimal("0.00")
                points_redeemed = 0
                if customer and customer.points >= 100 and random.random() < 0.1:
                    points_redeemed = min(customer.points, random.choice([100, 200, 300]))
                    loyalty_discount = Decimal(str(points_redeemed)) * rule.point_value
                    net_total = max(Decimal("0.00"), net_total - loyalty_discount)
                    
                    # Deduct points in loyalty transaction
                    lt = LoyaltyTransaction(
                        company_id=company.id,
                        customer_id=customer.id,
                        points=-points_redeemed,
                        type="redeem",
                        reference_id=str(sale.id),
                        description=f"Redeemed {points_redeemed} points on checkout"
                    )
                    db.add(lt)
                    customer.points -= points_redeemed

                # Award loyalty points for this sale
                if customer:
                    points_earned = int(net_total / rule.spend_amount) * rule.points_earned
                    if points_earned > 0:
                        lt_earn = LoyaltyTransaction(
                            company_id=company.id,
                            customer_id=customer.id,
                            points=points_earned,
                            type="earn",
                            reference_id=str(sale.id),
                            description=f"Earned points on invoice {invoice_no}"
                        )
                        db.add(lt_earn)
                        customer.points += points_earned

                sale.sub_total = sub_total
                sale.tax_amount = tax_total
                sale.discount_amount = discount_total
                sale.loyalty_points_redeemed = points_redeemed
                sale.loyalty_discount = loyalty_discount
                sale.net_amount = net_total
                sale.amount_paid = net_total
                sale.change_returned = Decimal("0.00")
                db.flush()

                # Add payments
                # 90% chance single payment method, 10% cash/card split
                if random.random() < 0.9:
                    pm = random.choice(payment_methods)
                    pay = Payment(
                        company_id=company.id,
                        branch_id=shift.branch_id,
                        sale_id=sale.id,
                        amount=net_total,
                        payment_method=pm,
                        transaction_reference=f"REF-{random.randint(100000, 999999)}" if pm != "CASH" else None
                    )
                    db.add(pay)
                else:
                    cash_part = (net_total / 2).quantize(Decimal("0.01"))
                    card_part = net_total - cash_part
                    
                    pay1 = Payment(
                        company_id=company.id,
                        branch_id=shift.branch_id,
                        sale_id=sale.id,
                        amount=cash_part,
                        payment_method="CASH"
                    )
                    pay2 = Payment(
                        company_id=company.id,
                        branch_id=shift.branch_id,
                        sale_id=sale.id,
                        amount=card_part,
                        payment_method="CARD",
                        transaction_reference=f"REF-{random.randint(100000, 999999)}"
                    )
                    db.add(pay1)
                    db.add(pay2)
                
                # 5% chance of sale cancellation (void override)
                if random.random() < 0.05:
                    sale.sale_status = "cancelled"
                    sale.payment_status = "refunded"
                    
                    # Create void audit log
                    al_void = AuditLog(
                        company_id=company.id,
                        user_id=random.choice(users).id, # Manager voiding it
                        action="sale_cancellation",
                        details={
                            "invoice_number": invoice_no,
                            "net_amount": float(net_total),
                            "reason": random.choice(["Customer changed mind", "Wrong pricing selected", "Order double billed"])
                        },
                        ip_address=f"192.168.1.{random.randint(10, 99)}",
                        created_at=sale_date + timedelta(minutes=5)
                    )
                    db.add(al_void)
                else:
                    # Standard checkout audit log
                    al_check = AuditLog(
                        company_id=company.id,
                        user_id=sale.user_id,
                        action="sale_checkout",
                        details={
                            "invoice_number": invoice_no,
                            "net_amount": float(net_total)
                        },
                        ip_address=f"192.168.1.{random.randint(10, 99)}",
                        created_at=sale_date
                    )
                    db.add(al_check)

                # Seed mock digital receipt dispatch logs
                if customer and random.random() < 0.6:
                    disp = NotificationDispatch(
                        company_id=company.id,
                        branch_id=sale.branch_id,
                        sale_id=sale.id,
                        type=random.choice(["email", "whatsapp"]),
                        recipient=customer.email if random.choice([True, False]) else customer.phone,
                        dispatch_status="sent",
                        created_at=sale_date + timedelta(seconds=30)
                    )
                    db.add(disp)

        print(f"Seeded {sales_count} sales transactions successfully.")

        print("Seeding Additional Audits for System Actions (Logins, Shift open/closes, etc.)...")
        additional_audits_count = 0
        
        # Seed 3 login and shift audits for each shift day to inflate audit logs list
        for shift in shifts:
            # Login action
            al_login = AuditLog(
                company_id=company.id,
                user_id=shift.user_id,
                action="login",
                details={"user_email": "admin@smartpos.com", "platform": "web_browser"},
                ip_address=f"192.168.1.{random.randint(10, 99)}",
                created_at=shift.created_at - timedelta(minutes=15)
            )
            db.add(al_login)

            # Shift open action
            al_so = AuditLog(
                company_id=company.id,
                user_id=shift.user_id,
                action="shift_open",
                details={"opening_balance": float(shift.opening_balance)},
                ip_address=f"192.168.1.{random.randint(10, 99)}",
                created_at=shift.created_at
            )
            db.add(al_so)

            # Shift close action
            al_sc = AuditLog(
                company_id=company.id,
                user_id=shift.user_id,
                action="shift_close",
                details={
                    "opening_balance": float(shift.opening_balance),
                    "expected_cash": float(shift.expected_cash),
                    "actual_cash": float(shift.actual_cash),
                    "variance": float(shift.variance)
                },
                ip_address=f"192.168.1.{random.randint(10, 99)}",
                created_at=shift.updated_at
            )
            db.add(al_sc)
            additional_audits_count += 3

        print(f"Seeded {additional_audits_count} additional system activity logs.")

        db.commit()
        print("\n=== SUCCESS: Seeding more transactional data completed successfully! ===")
    except Exception as e:
        db.rollback()
        print(f"Error during transaction seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seeding()
