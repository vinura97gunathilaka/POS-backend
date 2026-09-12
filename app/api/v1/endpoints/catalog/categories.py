from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.catalog.category import Category
from app.schemas.catalog.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/categories", response_model=APIResponse[List[CategoryOut]])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Category).filter(Category.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Category.company_id == current_user.company_id)
    categories = query.all()
    return APIResponse(data=categories)

@router.post("/categories", response_model=APIResponse[CategoryOut])
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    category = Category(**payload.model_dump(), created_by=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return APIResponse(data=category)

@router.put("/categories/{id}", response_model=APIResponse[CategoryOut])
def update_category(
    id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == id, Category.deleted_at == None).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if not current_user.is_superadmin and category.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, val)
    category.updated_by = current_user.id
    db.commit()
    db.refresh(category)
    return APIResponse(data=category)

@router.delete("/categories/{id}", response_model=APIResponse[str])
def delete_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == id, Category.deleted_at == None).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if not current_user.is_superadmin and category.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    category.deleted_at = func.now()
    category.status = "archived"
    category.updated_by = current_user.id
    db.commit()
    return APIResponse(data="Category deleted successfully.")
