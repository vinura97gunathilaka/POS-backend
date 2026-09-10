from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.organization import Branch
from app.models.catalog import Category, Product, ProductVariant, ProductVariantComponent
from app.models.inventory import Inventory
from app.schemas.catalog import (
    CategoryCreate, CategoryUpdate, CategoryOut,
    ProductCreate, ProductUpdate, ProductOut,
    ProductVariantComponentCreate, ProductVariantComponentOut
)
from app.schemas.response import APIResponse

router = APIRouter()

# --- Categories ---
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

    category = Category(**payload.dict(), created_by=current_user.id)
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

    for key, val in payload.dict(exclude_unset=True).items():
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


# --- Products ---
@router.get("/products", response_model=APIResponse[List[ProductOut]])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product).filter(Product.deleted_at == None)
    if not current_user.is_superadmin:
        query = query.filter(Product.company_id == current_user.company_id)
    products = query.all()
    return APIResponse(data=products)

@router.post("/products", response_model=APIResponse[ProductOut])
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin and current_user.company_id != payload.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create Product
    product_dict = payload.dict(exclude={"variants"})
    product = Product(**product_dict, created_by=current_user.id)
    db.add(product)
    db.flush()

    # Get branches for inventory initialization
    branches = db.query(Branch).filter(Branch.company_id == payload.company_id, Branch.deleted_at == None).all()

    # Create variants
    for var_data in payload.variants:
        variant = ProductVariant(
            company_id=payload.company_id,
            product_id=product.id,
            name=var_data.name,
            sku=var_data.sku,
            barcode=var_data.barcode,
            price=var_data.price,
            cost=var_data.cost,
            attributes=var_data.attributes,
            created_by=current_user.id
        )
        db.add(variant)
        db.flush()

        # Initialize stock across all branches to 0
        for br in branches:
            inv = Inventory(
                company_id=payload.company_id,
                branch_id=br.id,
                product_variant_id=variant.id,
                quantity=0,
                avg_cost=variant.cost,
                created_by=current_user.id
            )
            db.add(inv)

    db.commit()
    db.refresh(product)
    return APIResponse(data=product)

@router.get("/products/{id}", response_model=APIResponse[ProductOut])
def get_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not current_user.is_superadmin and product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return APIResponse(data=product)

@router.put("/products/{id}", response_model=APIResponse[ProductOut])
def update_product(
    id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not current_user.is_superadmin and product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    for key, val in payload.dict(exclude_unset=True).items():
        setattr(product, key, val)
    product.updated_by = current_user.id
    db.commit()
    db.refresh(product)
    return APIResponse(data=product)

@router.delete("/products/{id}", response_model=APIResponse[str])
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not current_user.is_superadmin and product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    product.deleted_at = func.now()
    product.status = "archived"
    product.updated_by = current_user.id
    db.commit()
    return APIResponse(data="Product deactivated successfully.")

# --- Manage Variant Recipe (BOM) ---
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
        # Verify component variant exists and is from the same company
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


