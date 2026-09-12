from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.auth import AuditBase
from app.schemas.catalog.product_variant import ProductVariantCreate, ProductVariantOut

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    image_url: Optional[str] = None
    tax_rate: Decimal = Decimal("0.00")
    type: str = "product"  # product, service, combo
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
