"""
app.services.catalog_service
------------------------------
Business logic for product catalog management.

Responsibilities:
  - Category CRUD with company scoping
  - Product and variant creation with validation
  - Barcode / SKU uniqueness enforcement
  - Bill-of-Materials (BOM) / recipe component management
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.repositories.catalog_repository import (
    CategoryRepository,
    ProductRepository,
    ProductVariantRepository,
    ProductVariantComponentRepository,
)

logger = get_logger(__name__)


class CatalogService:
    """Manages product catalog business rules."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.category_repo = CategoryRepository(db)
        self.product_repo = ProductRepository(db)
        self.variant_repo = ProductVariantRepository(db)
        self.component_repo = ProductVariantComponentRepository(db)

    def assert_barcode_unique(self, barcode: str, exclude_id: Optional[int] = None) -> None:
        """Raise 409 if the barcode is already in use by another variant."""
        existing = self.variant_repo.get_by_barcode(barcode)
        if existing and existing.id != exclude_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Barcode '{barcode}' is already assigned to another product variant.",
            )

    def assert_sku_unique(self, sku: str, exclude_id: Optional[int] = None) -> None:
        """Raise 409 if the SKU is already in use."""
        existing = self.variant_repo.get_by_sku(sku)
        if existing and existing.id != exclude_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"SKU '{sku}' is already assigned to another product variant.",
            )
