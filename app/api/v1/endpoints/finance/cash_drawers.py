from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.finance.cash_drawer import CashDrawer
from app.schemas.finance.cash_drawer import CashDrawerCreate, CashDrawerOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/cash-drawers", response_model=APIResponse[List[CashDrawerOut]])
def list_cash_drawers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CashDrawer).filter(CashDrawer.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(CashDrawer.company_id == current_user.company_id)
    drawers = query.all()
    return APIResponse(data=drawers)

@router.post("/cash-drawers", response_model=APIResponse[CashDrawerOut])
def create_cash_drawer(
    payload: CashDrawerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    drawer = CashDrawer(**payload.model_dump(), created_by=current_user.id)
    db.add(drawer)
    db.commit()
    db.refresh(drawer)
    return APIResponse(data=drawer)
