from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.logging.audit_log import AuditLog
from app.schemas.logging.audit_log import AuditLogOut, AuditStatsOut
from app.services.logging.audit_service import AuditService
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/audit-logs", response_model=APIResponse[List[AuditLogOut]])
def list_audit_logs(
    response: Response,
    action: Optional[str] = None,
    model_name: Optional[str] = None,
    record_id: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_id = None if current_user.is_superadmin else current_user.company_id
    logs, total, pages = AuditService.get_audit_logs(
        db,
        company_id=company_id,
        action=action,
        model_name=model_name,
        record_id=record_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        limit=limit
    )

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Total-Pages"] = str(pages)
    response.headers["X-Current-Page"] = str(page)
    response.headers["X-Page-Limit"] = str(limit)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages, X-Current-Page, X-Page-Limit"

    return APIResponse(data=logs)

@router.get("/audit-logs/stats/summary", response_model=APIResponse[AuditStatsOut])
def get_audit_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_id = None if current_user.is_superadmin else current_user.company_id
    stats = AuditService.get_statistics(db, company_id=company_id)
    return APIResponse(data=stats)

@router.get("/audit-logs/export/csv")
def export_audit_logs(
    action: Optional[str] = None,
    model_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_id = None if current_user.is_superadmin else current_user.company_id
    csv_data = AuditService.export_csv(
        db,
        company_id=company_id,
        action=action,
        model_name=model_name,
        date_from=date_from,
        date_to=date_to
    )
    filename = f"audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/audit-logs/entity/{model_name}/{record_id}", response_model=APIResponse[List[AuditLogOut]])
def get_entity_audit_trail(
    model_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_id = None if current_user.is_superadmin else current_user.company_id
    history = AuditService.get_record_history(
        db,
        model_name=model_name,
        record_id=record_id,
        company_id=company_id
    )
    return APIResponse(data=history)

@router.get("/audit-logs/{id}", response_model=APIResponse[AuditLogOut])
def get_audit_log_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AuditLog).filter(AuditLog.id == id)
    if not current_user.is_superadmin:
        query = query.filter(AuditLog.company_id == current_user.company_id)
    log = query.first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return APIResponse(data=log)
