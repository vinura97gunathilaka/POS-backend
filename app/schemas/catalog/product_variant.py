from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

class ProductVariantBase(BaseModel):
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Decimal
    cost: Decimal
    attributes: Dict[str, Any] = {}

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    attributes: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class ProductVariantInventoryOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    product_variant_id: int
    quantity: int
    avg_cost: Decimal
    location_bin: Optional[str] = None

    class Config:
        from_attributes = True

class ProductVariantProductOut(BaseModel):
    id: int
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None

    class Config:
        from_attributes = True

class ProductVariantComponentCreate(BaseModel):
    component_variant_id: int
    quantity: int

class ComponentVariantDetails(BaseModel):
    id: int
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Decimal
    cost: Decimal

    class Config:
        from_attributes = True

class ProductVariantComponentOut(BaseModel):
    id: int
    company_id: int
    parent_variant_id: int
    component_variant_id: int
    quantity: int
    component_variant: Optional[ComponentVariantDetails] = None

    class Config:
        from_attributes = True

class ProductVariantOut(ProductVariantBase, AuditBase):
    company_id: int
    product_id: int
    product: Optional[ProductVariantProductOut] = None
    inventories: List[ProductVariantInventoryOut] = []
    recipe_components: List[ProductVariantComponentOut] = []
