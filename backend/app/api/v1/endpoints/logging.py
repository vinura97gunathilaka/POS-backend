from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import math

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.rbac import User
from app.models.logging import Notification, AuditLog, NotificationDispatch
from app.schemas.logging import NotificationOut, AuditLogOut, NotificationDispatchOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/notifications", response_model=APIResponse[List[NotificationOut]])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Notification).filter(Notification.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Notification.company_id == current_user.company_id)
    notifications = query.all()
    return APIResponse(data=notifications)

@router.put("/notifications/{id}/read", response_model=APIResponse[NotificationOut])
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(Notification.id == id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not current_user.is_superadmin and notification.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return APIResponse(data=notification)

@router.get("/audit-logs", response_model=APIResponse[List[AuditLogOut]])
def list_audit_logs(
    response: Response,
    action: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AuditLog)
    if not current_user.is_superadmin:
        query = query.filter(AuditLog.company_id == current_user.company_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    # Order by newest first
    query = query.order_by(AuditLog.created_at.desc())

    if page is not None and limit is not None:
        total = query.count()
        pages = math.ceil(total / limit) if limit > 0 else 0
        skip = (page - 1) * limit
        logs = query.offset(skip).limit(limit).all()
        
        # Expose and set custom pagination headers
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Total-Pages"] = str(pages)
        response.headers["X-Current-Page"] = str(page)
        response.headers["X-Page-Limit"] = str(limit)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages, X-Current-Page, X-Page-Limit"
    else:
        logs = query.all()
        
    return APIResponse(data=logs)

@router.get("/notification-dispatches", response_model=APIResponse[List[NotificationDispatchOut]])
def list_notification_dispatches(
    response: Response,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(NotificationDispatch)
    if not current_user.is_superadmin:
        query = query.filter(NotificationDispatch.company_id == current_user.company_id)
    
    query = query.order_by(NotificationDispatch.created_at.desc())
    
    if page is not None and limit is not None:
        total = query.count()
        pages = math.ceil(total / limit) if limit > 0 else 0
        skip = (page - 1) * limit
        dispatches = query.offset(skip).limit(limit).all()
        
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Total-Pages"] = str(pages)
        response.headers["X-Current-Page"] = str(page)
        response.headers["X-Page-Limit"] = str(limit)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages, X-Current-Page, X-Page-Limit"
    else:
        dispatches = query.all()
        
    return APIResponse(data=dispatches)

