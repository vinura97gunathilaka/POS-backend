from fastapi import APIRouter
from app.api.v1.endpoints.finance.shifts import router as shifts_router
from app.api.v1.endpoints.finance.cash_drawers import router as cash_drawers_router
from app.api.v1.endpoints.finance.expenses import router as expenses_router
from app.api.v1.endpoints.finance.bank_accounts import router as bank_accounts_router

router = APIRouter()
router.include_router(shifts_router)
router.include_router(cash_drawers_router)
router.include_router(expenses_router)
router.include_router(bank_accounts_router)

__all__ = ["router"]
