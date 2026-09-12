from fastapi import APIRouter
from app.api.v1.endpoints.crm.customers import router as customers_router
from app.api.v1.endpoints.crm.suppliers import router as suppliers_router
from app.api.v1.endpoints.crm.loyalty import router as loyalty_router

router = APIRouter()
router.include_router(customers_router)
router.include_router(suppliers_router)
router.include_router(loyalty_router)

__all__ = ["router"]
