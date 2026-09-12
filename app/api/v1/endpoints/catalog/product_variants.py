from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.catalog.product_variant import ProductVariant
from app.models.catalog.product_variant_component import ProductVariantComponent
from app.schemas.catalog.product_variant import ProductVariantComponentCreate, ProductVariantComponentOut
from app.schemas.response import APIResponse

router = APIRouter()

@router.put("/variants/{id}/recipe", response_model=APIResponse[List[ProductVariantComponentOut]])
def update_variant_recipe(
    id: int,
    payload: List[ProductVariantComponentCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")
    
    if not current_user.is_superadmin and variant.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Clear existing recipe components
    db.query(ProductVariantComponent).filter(ProductVariantComponent.parent_variant_id == id).delete()

    # Create new components
    for comp in payload:
        comp_var = db.query(ProductVariant).filter(ProductVariant.id == comp.component_variant_id).first()
        if not comp_var:
            raise HTTPException(status_code=404, detail=f"Component variant ID {comp.component_variant_id} not found")
        if comp_var.company_id != variant.company_id:
            raise HTTPException(status_code=403, detail="Ingredient component must belong to the same company")
        if comp_var.id == variant.id:
            raise HTTPException(status_code=400, detail="A variant cannot be an ingredient of itself")

        db_comp = ProductVariantComponent(
            company_id=variant.company_id,
            parent_variant_id=variant.id,
            component_variant_id=comp.component_variant_id,
            quantity=comp.quantity,
            created_by=current_user.id
        )
        db.add(db_comp)

    db.commit()
    db.refresh(variant)
    return APIResponse(data=variant.recipe_components)

@router.get("/variants/{id}/recipe", response_model=APIResponse[List[ProductVariantComponentOut]])
def get_variant_recipe(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")
    
    if not current_user.is_superadmin and variant.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return APIResponse(data=variant.recipe_components)
