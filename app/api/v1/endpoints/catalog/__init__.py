from fastapi import APIRouter
from app.api.v1.endpoints.catalog.categories import router as categories_router
from app.api.v1.endpoints.catalog.products import router as products_router
from app.api.v1.endpoints.catalog.product_variants import router as product_variants_router

router = APIRouter()
router.include_router(categories_router)
router.include_router(products_router)
router.include_router(product_variants_router)

__all__ = ["router"]
