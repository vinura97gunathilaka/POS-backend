from fastapi import APIRouter
from app.api.v1.endpoints.sales.sales import (
    router as sales_router,
    checkout,
    cancel_sale,
    list_sales,
    list_held_sales,
)
from app.api.v1.endpoints.sales.kds import (
    router as kds_router,
    list_kds_queue,
    update_kds_status,
    list_public_kds_queue,
    kds_broadcaster,
)
from app.api.v1.endpoints.sales.csat_feedback import (
    router as csat_router,
    submit_receipt_feedback,
)
from app.api.v1.endpoints.sales.receipt_dispatches import (
    router as dispatches_router,
    get_public_receipt,
    dispatch_receipt,
)

router = APIRouter()
router.include_router(sales_router)
router.include_router(kds_router)
router.include_router(csat_router)
router.include_router(dispatches_router)

__all__ = [
    "router",
    "checkout",
    "cancel_sale",
    "list_sales",
    "list_held_sales",
    "list_kds_queue",
    "update_kds_status",
    "list_public_kds_queue",
    "submit_receipt_feedback",
    "get_public_receipt",
    "dispatch_receipt",
    "kds_broadcaster",
]
