from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.finance.bank_account import BankAccount
from app.schemas.finance.bank_account import BankAccountCreate, BankAccountOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/bank-accounts", response_model=APIResponse[List[BankAccountOut]])
def list_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(BankAccount).filter(BankAccount.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(BankAccount.company_id == current_user.company_id)
    accounts = query.all()
    return APIResponse(data=accounts)

@router.post("/bank-accounts", response_model=APIResponse[BankAccountOut])
def create_bank_account(
    payload: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = BankAccount(**payload.model_dump(), created_by=current_user.id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return APIResponse(data=account)
