from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.finance.expense_category import ExpenseCategory
from app.models.finance.expense import Expense
from app.schemas.finance.expense_category import ExpenseCategoryCreate, ExpenseCategoryOut
from app.schemas.finance.expense import ExpenseCreate, ExpenseOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/expenses/categories", response_model=APIResponse[List[ExpenseCategoryOut]])
def list_expense_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ExpenseCategory).filter(ExpenseCategory.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(ExpenseCategory.company_id == current_user.company_id)
    categories = query.all()
    return APIResponse(data=categories)

@router.post("/expenses/categories", response_model=APIResponse[ExpenseCategoryOut])
def create_expense_category(
    payload: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = ExpenseCategory(**payload.model_dump(), created_by=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return APIResponse(data=category)

@router.get("/expenses", response_model=APIResponse[List[ExpenseOut]])
def list_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Expense).filter(Expense.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Expense.company_id == current_user.company_id)
    expenses = query.all()
    return APIResponse(data=expenses)

@router.post("/expenses", response_model=APIResponse[ExpenseOut])
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = Expense(**payload.model_dump(), created_by=current_user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return APIResponse(data=expense)
