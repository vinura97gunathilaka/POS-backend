from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth.user import User
from app.models.organization.branch import Branch
from app.models.catalog.product import Product
from app.models.catalog.product_variant import ProductVariant
from app.models.inventory.inventory import Inventory
from app.schemas.catalog.product import ProductCreate, ProductUpdate, ProductOut
from app.schemas.response import APIResponse

router = APIRouter()

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
    product_dict = payload.model_dump(exclude={"variants"})
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

    for key, val in payload.model_dump(exclude_unset=True).items():
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
