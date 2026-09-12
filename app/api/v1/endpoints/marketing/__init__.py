from fastapi import APIRouter
from app.api.v1.endpoints.marketing.promotions import router as promotions_router
from app.api.v1.endpoints.marketing.vouchers import router as vouchers_router

router = APIRouter()
router.include_router(promotions_router)
router.include_router(vouchers_router)

__all__ = ["router"]
