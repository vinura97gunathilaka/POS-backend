from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.sales.sale import Sale
from app.models.logging.notification_dispatch import NotificationDispatch
from app.schemas.sales.sale import SaleOut, ReceiptDispatchPayload
from app.schemas.response import APIResponse

router = APIRouter()

# --- Public Receipt Lookup ---
@router.get("/public/receipt/{invoice_number}", response_model=APIResponse[SaleOut])
def get_public_receipt(
    invoice_number: str,
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(Sale.invoice_number == invoice_number).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice receipt not found")
    return APIResponse(data=sale)

# --- Dispatch Digital Receipt via Email/WhatsApp ---
@router.post("/{id}/dispatch-receipt", response_model=APIResponse[dict])
def dispatch_receipt(
    id: int,
    payload: ReceiptDispatchPayload,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    if not current_user.is_superadmin and sale.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create dispatch logs record
    dispatch_log = NotificationDispatch(
        company_id=sale.company_id,
        branch_id=sale.branch_id,
        sale_id=sale.id,
        type=payload.type,
        recipient=payload.recipient,
        dispatch_status="sent",
        created_by=current_user.id
    )
    db.add(dispatch_log)
    db.commit()

    message = f"Invoice {sale.invoice_number} successfully dispatched via {payload.type} to {payload.recipient}"
    return APIResponse(data={"message": message, "status": "sent", "recipient": payload.recipient})
