from fastapi import APIRouter
from app.api.v1.endpoints.procurement.grn import router as grn_router
from app.api.v1.endpoints.procurement.purchases import router as purchases_router

router = APIRouter()
router.include_router(grn_router)
router.include_router(purchases_router)

__all__ = ["router"]
