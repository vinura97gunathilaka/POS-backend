from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase

# --- Category ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    company_id: int

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    status: Optional[str] = None

class CategoryOut(CategoryBase, AuditBase):
    company_id: int

# --- Product Variant ---
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


# --- Product ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    image_url: Optional[str] = None
    tax_rate: Decimal = Decimal("0.00")
    type: str = "product" # product, service, combo
    track_inventory: bool = True
    reorder_level: int = 10

class ProductCreate(ProductBase):
    company_id: int
    category_id: Optional[int] = None
    variants: List[ProductVariantCreate] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    image_url: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    type: Optional[str] = None
    track_inventory: Optional[bool] = None
    reorder_level: Optional[int] = None
    status: Optional[str] = None

class ProductOut(ProductBase, AuditBase):
    company_id: int
    category_id: Optional[int] = None
    variants: List[ProductVariantOut] = []

