import sys
from app.core.database import SessionLocal
from app.models.rbac import Company, User, Branch
from app.models.sales import Sale, CSATFeedback
from app.schemas.sales import CSATFeedbackCreate
from app.api.v1.endpoints.sales import submit_receipt_feedback
from app.api.v1.endpoints.analytics import list_csat_feedbacks

def run_tests():
    db = SessionLocal()
    print("Starting Customer Satisfaction Feedback (CSAT) integration validation tests...")

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
        print("FAIL: No sale found in DB to run CSAT test!")
        return False

    # Clean any existing feedback for this sale to ensure clean run
    existing = db.query(CSATFeedback).filter(CSATFeedback.sale_id == sale.id).first()
    if existing:
        db.delete(existing)
        db.commit()

    # TEST 1: Submit valid CSAT Feedback (5 Stars)
    print("\n--- Test 1: Submit CSAT Feedback (5 Stars) ---")
    payload = CSATFeedbackCreate(rating=5, feedback_text="Amazing service!")
    res1 = submit_receipt_feedback(invoice_number=sale.invoice_number, payload=payload, db=db)
    print(f"Feedback response: {res1.data}")
    if res1.data["message"] != "Feedback submitted successfully":
        print("FAIL: Expected feedback to submit successfully")
        return False
    print("PASS: Test 1 Succeeded!")

    # TEST 2: Double-submission block
    print("\n--- Test 2: Double-submission Block ---")
    try:
        submit_receipt_feedback(invoice_number=sale.invoice_number, payload=payload, db=db)
        print("FAIL: Double submission did not throw an exception!")
        return False
    except Exception as e:
        print(f"Intercepted expected error: {e}")
        print("PASS: Test 2 Succeeded!")

    # TEST 3: Invalid rating range block
    print("\n--- Test 3: Invalid Rating Range Block ---")
    sale2 = db.query(Sale).filter(Sale.company_id == company.id, Sale.id != sale.id).first()
    if sale2:
        try:
            bad_payload = CSATFeedbackCreate(rating=6, feedback_text="Super awesome")
            submit_receipt_feedback(invoice_number=sale2.invoice_number, payload=bad_payload, db=db)
            print("FAIL: Rating of 6 did not throw an exception!")
            return False
        except Exception as e:
            print(f"Intercepted expected error: {e}")
            print("PASS: Test 3 Succeeded!")
    else:
        print("Skipping Test 3 (no second sale available for test).")

    # TEST 4: Query CSAT Feedback Analytics
    print("\n--- Test 4: Query CSAT Feedback Analytics ---")
    res4 = list_csat_feedbacks(page=1, limit=10, db=db, current_user=user)
    csat_analytics = res4.data
    print(f"CSAT Summary: {csat_analytics['summary']}")
    print(f"Found {len(csat_analytics['feedbacks'])} CSAT feedbacks.")
    
    # Check that our created feedback is present in the feed
    feedback_logged = any(f["sale_id"] == sale.id and f["rating"] == 5 and f["feedback_text"] == "Amazing service!" for f in csat_analytics["feedbacks"])
    if not feedback_logged:
        print("FAIL: Feedback was not found in analytics list!")
        return False
    print("PASS: Test 4 Succeeded!")

    print("\nALL CUSTOMER SATISFACTION FEEDBACK (CSAT) INTEGRATION TESTS PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
