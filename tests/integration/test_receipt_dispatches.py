import sys
from app.core.database import SessionLocal
from app.models.auth import User
from app.models.organization import Company, Branch
from app.models.sales import Sale
from app.models.logging import NotificationDispatch
from app.schemas.sales import ReceiptDispatchPayload
from app.api.v1.endpoints.sales import get_public_receipt, dispatch_receipt
from app.api.v1.endpoints.logging import list_notification_dispatches

def run_tests():
    db = SessionLocal()
    print("Starting Digital Receipts & Notification Dispatches integration validation tests...")

    # Fetch company, branch, user and sale
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

    sale = db.query(Sale).filter(Sale.company_id == company.id).first()
    if not sale:
        print("FAIL: No sale found in DB to run dispatch test!")
        return False

    # TEST 1: Public Receipt Lookup (should be open without authentication)
    print("\n--- Test 1: Public Receipt Lookup ---")
    res1 = get_public_receipt(invoice_number=sale.invoice_number, db=db)
    public_sale = res1.data
    print(f"Loaded Public Invoice: {public_sale.invoice_number}")
    if public_sale.id != sale.id:
        print(f"FAIL: Expected sale ID {sale.id}, got {public_sale.id}")
        return False
    print("PASS: Test 1 Succeeded!")

    # TEST 2: Dispatch receipt via Email
    print("\n--- Test 2: Dispatch Receipt via Email ---")
    payload_email = ReceiptDispatchPayload(type="email", recipient="customer@gmail.com")
    res2 = dispatch_receipt(id=sale.id, payload=payload_email, db=db, current_user=user)
    print(f"Dispatch response: {res2.data}")
    if res2.data["status"] != "sent" or "customer@gmail.com" not in res2.data["message"]:
        print("FAIL: Expected email dispatch status to be 'sent' and contain the recipient")
        return False
    print("PASS: Test 2 Succeeded!")

    # TEST 3: Dispatch receipt via WhatsApp
    print("\n--- Test 3: Dispatch Receipt via WhatsApp ---")
    payload_wa = ReceiptDispatchPayload(type="whatsapp", recipient="+94771234567")
    res3 = dispatch_receipt(id=sale.id, payload=payload_wa, db=db, current_user=user)
    print(f"Dispatch response: {res3.data}")
    if res3.data["status"] != "sent" or "+94771234567" not in res3.data["message"]:
        print("FAIL: Expected WhatsApp dispatch status to be 'sent' and contain the recipient")
        return False
    print("PASS: Test 3 Succeeded!")

    # TEST 4: Query outbound notification dispatches
    print("\n--- Test 4: Query Outbound Notification Dispatches ---")
    res4 = list_notification_dispatches(db=db, current_user=user)
    logs = res4.data
    print(f"Found {len(logs)} dispatch log entries.")
    # Check that our latest dispatches exist
    email_logged = any(log.type == "email" and log.recipient == "customer@gmail.com" and log.sale_id == sale.id for log in logs)
    wa_logged = any(log.type == "whatsapp" and log.recipient == "+94771234567" and log.sale_id == sale.id for log in logs)
    
    print(f"Email dispatch logged: {email_logged}")
    print(f"WhatsApp dispatch logged: {wa_logged}")
    if not email_logged or not wa_logged:
        print("FAIL: Dispatches were not logged in notification_dispatches table!")
        return False
    print("PASS: Test 4 Succeeded!")

    print("\nALL DIGITAL RECEIPT & DISPATCH LOG INTEGRATION TESTS PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

