import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.organization.company import Company
from app.models.sales.sale import Sale
from app.schemas.sales.sale import SaleOut, SaleUpdate
from app.schemas.response import APIResponse

router = APIRouter()

class KDSBroadcaster:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, company_id: int) -> asyncio.Queue:
        queue = asyncio.Queue()
        if company_id not in self.listeners:
            self.listeners[company_id] = []
        self.listeners[company_id].append(queue)
        return queue

    def unsubscribe(self, company_id: int, queue: asyncio.Queue):
        if company_id in self.listeners:
            if queue in self.listeners[company_id]:
                self.listeners[company_id].remove(queue)
            if not self.listeners[company_id]:
                del self.listeners[company_id]

    def broadcast(self, company_id: int, event_type: str, data: dict = None):
        if company_id in self.listeners:
            for queue in self.listeners[company_id]:
                queue.put_nowait({"event": event_type, "data": data or {}})

kds_broadcaster = KDSBroadcaster()

# --- Public KDS Queue ---
@router.get("/kds/public", response_model=APIResponse[List[dict]])
def list_public_kds_queue(
    company_id: int,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    enable_kds = company.settings.get("enable_kds", False)
    if not enable_kds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order Prep Monitor (KDS Queue) is currently disabled. Please enable it under System Configurations in the dashboard."
        )

    query = db.query(Sale).filter(
        Sale.company_id == company_id,
        Sale.preparation_status.in_(["pending", "preparing", "ready"]),
        Sale.deleted_at == None
    )
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)
        
    sales = query.order_by(Sale.sale_date.asc()).all()
    
    result = []
    for s in sales:
        parts = s.invoice_number.split('-')
        queue_no = parts[-1] if parts else s.invoice_number
        
        result.append({
            "id": s.id,
            "invoice_number": s.invoice_number,
            "queue_number": queue_no,
            "preparation_status": s.preparation_status,
            "sale_date": s.sale_date.isoformat()
        })
        
    return APIResponse(data=result)

# --- KDS Active Queue ---
@router.get("/kds/queue", response_model=APIResponse[List[SaleOut]])
def list_kds_queue(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale).filter(
        Sale.preparation_status.in_(["pending", "preparing", "ready"]),
        Sale.deleted_at == None
    )
    if not current_user.is_superadmin:
        query = query.filter(Sale.company_id == current_user.company_id)
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
    elif branch_id:
        query = query.filter(Sale.branch_id == branch_id)
    
    sales = query.order_by(Sale.sale_date.asc()).all()
    return APIResponse(data=sales)

# --- Update KDS Prep Status ---
@router.put("/{id}/kds-status", response_model=APIResponse[SaleOut])
def update_kds_status(
    id: int,
    payload: SaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    
    if not current_user.is_superadmin and sale.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if payload.preparation_status not in ["pending", "preparing", "ready", "completed", "none"]:
        raise HTTPException(status_code=400, detail="Invalid preparation status value")
        
    sale.preparation_status = payload.preparation_status
    sale.updated_by = current_user.id
    db.commit()
    db.refresh(sale)
    kds_broadcaster.broadcast(sale.company_id, "refresh")
    return APIResponse(data=sale)

# --- Public KDS Server-Sent Events Route ---
@router.get("/kds/events", response_class=StreamingResponse)
async def kds_events(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted_at == None).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    queue = kds_broadcaster.subscribe(company_id)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'event': 'connected'})}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'ping'})}\n\n"
        finally:
            kds_broadcaster.unsubscribe(company_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
