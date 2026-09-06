from fastapi import APIRouter
from app.api.v1.endpoints import auth, companies, branches, users, catalog, crm, inventory, sales, finance, logging, procurement, analytics, marketing

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(crm.router, prefix="/crm", tags=["crm"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(logging.router, prefix="/logging", tags=["logging"])
api_router.include_router(procurement.router, prefix="/procurement", tags=["procurement"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(marketing.router, prefix="/marketing", tags=["marketing"])
