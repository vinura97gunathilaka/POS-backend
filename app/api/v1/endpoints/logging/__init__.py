from fastapi import APIRouter
from app.api.v1.endpoints.logging.notifications import (
    router as notifications_router,
    list_notification_dispatches,
)
from app.api.v1.endpoints.logging.audit_logs import router as audit_logs_router

router = APIRouter()
router.include_router(notifications_router)
router.include_router(audit_logs_router)

__all__ = ["router", "list_notification_dispatches"]
