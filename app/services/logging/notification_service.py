"""
app.services.logging.notification_service
------------------------------------------
Service for creating, querying, and marking notifications,
as well as managing dispatch logs for digital receipts.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.logging.notification import Notification
from app.models.logging.notification_dispatch import NotificationDispatch

class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        company_id: int,
        title: str,
        message: str,
        notification_type: str,
        branch_id: Optional[int] = None
    ) -> Notification:
        notification = Notification(
            company_id=company_id,
            branch_id=branch_id,
            title=title,
            message=message,
            type=notification_type,
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def list_notifications(
        db: Session,
        company_id: int,
        branch_id: Optional[int] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.company_id == company_id)
        if branch_id:
            query = query.filter(
                (Notification.branch_id == branch_id) | (Notification.branch_id == None)
            )
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(desc(Notification.created_at)).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> Optional[Notification]:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)
        return notification

    @staticmethod
    def record_dispatch(
        db: Session,
        company_id: int,
        branch_id: int,
        sale_id: int,
        dispatch_type: str,
        recipient: str,
        status: str = "sent",
        error_message: Optional[str] = None
    ) -> NotificationDispatch:
        dispatch = NotificationDispatch(
            company_id=company_id,
            branch_id=branch_id,
            sale_id=sale_id,
            type=dispatch_type,
            recipient=recipient,
            dispatch_status=status,
            error_message=error_message
        )
        db.add(dispatch)
        db.commit()
        db.refresh(dispatch)
        return dispatch
