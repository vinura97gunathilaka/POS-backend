from fastapi import APIRouter
from app.api.v1.endpoints.inventory.inventory import router as inventory_router
from app.api.v1.endpoints.inventory.stock_transfers import router as transfers_router

router = APIRouter()
router.include_router(inventory_router)
router.include_router(transfers_router)

__all__ = ["router"]
