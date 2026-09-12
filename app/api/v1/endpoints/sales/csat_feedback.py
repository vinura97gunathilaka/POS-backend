from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sales.sale import Sale
from app.models.sales.csat_feedback import CSATFeedback
from app.schemas.sales.csat_feedback import CSATFeedbackCreate
from app.schemas.response import APIResponse

router = APIRouter()

# --- Public CSAT Feedback Submission ---
@router.post("/public/receipt/{invoice_number}/feedback", response_model=APIResponse[dict])
def submit_receipt_feedback(
    invoice_number: str,
    payload: CSATFeedbackCreate,
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(Sale.invoice_number == invoice_number).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Check if feedback already exists
    existing = db.query(CSATFeedback).filter(CSATFeedback.sale_id == sale.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted for this transaction")
    
    feedback = CSATFeedback(
        company_id=sale.company_id,
        branch_id=sale.branch_id,
        sale_id=sale.id,
        rating=payload.rating,
        feedback_text=payload.feedback_text
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return APIResponse(data={"message": "Feedback submitted successfully", "id": feedback.id})
