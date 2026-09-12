from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.crm.customer import Customer
from app.models.crm.loyalty_rule import LoyaltyRule
from app.models.crm.loyalty_transaction import LoyaltyTransaction
from app.schemas.crm.loyalty_rule import LoyaltyRuleCreate, LoyaltyRuleOut
from app.schemas.crm.loyalty_transaction import LoyaltyTransactionOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/loyalty/rules", response_model=APIResponse[List[LoyaltyRuleOut]])
def list_loyalty_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(LoyaltyRule).filter(LoyaltyRule.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(LoyaltyRule.company_id == current_user.company_id)
    rules = query.all()
    return APIResponse(data=rules)

@router.post("/loyalty/rules", response_model=APIResponse[LoyaltyRuleOut])
def create_loyalty_rule(
    payload: LoyaltyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    rule = LoyaltyRule(**payload.model_dump(), created_by=current_user.id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return APIResponse(data=rule)

@router.get("/loyalty/transactions/{customer_id}", response_model=APIResponse[List[LoyaltyTransactionOut]])
def list_loyalty_transactions(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not current_user.is_superadmin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    transactions = db.query(LoyaltyTransaction).filter(LoyaltyTransaction.customer_id == customer_id).all()
    return APIResponse(data=transactions)
