"""
app.repositories.catalog_repository
--------------------------------------
Data access layer for Category, Product, and ProductVariant entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.catalog import Category, Product, ProductVariant, ProductVariantComponent


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session) -> None:
        super().__init__(Category, db)

    def get_by_company(self, company_id: int) -> List[Category]:
        return (
            self.db.query(Category)
            .filter(Category.company_id == company_id, Category.status == "active")
            .all()
        )


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session) -> None:
        super().__init__(Product, db)

    def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        return (
            self.db.query(Product)
            .filter(Product.company_id == company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, company_id: int, query: str) -> List[Product]:
        pattern = f"%{query}%"
        return (
            self.db.query(Product)
            .filter(
                Product.company_id == company_id,
                Product.name.ilike(pattern),
            )
            .all()
        )


class ProductVariantRepository(BaseRepository[ProductVariant]):
    def __init__(self, db: Session) -> None:
        super().__init__(ProductVariant, db)

    def get_by_barcode(self, barcode: str) -> Optional[ProductVariant]:
        return (
            self.db.query(ProductVariant)
            .filter(ProductVariant.barcode == barcode)
            .first()
        )

    def get_by_sku(self, sku: str) -> Optional[ProductVariant]:
        return (
            self.db.query(ProductVariant)
            .filter(ProductVariant.sku == sku)
            .first()
        )

    def get_by_product(self, product_id: int) -> List[ProductVariant]:
        return (
            self.db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id)
            .all()
        )


class ProductVariantComponentRepository(BaseRepository[ProductVariantComponent]):
    def __init__(self, db: Session) -> None:
        super().__init__(ProductVariantComponent, db)

    def get_by_variant(self, variant_id: int) -> List[ProductVariantComponent]:
        return (
            self.db.query(ProductVariantComponent)
            .filter(ProductVariantComponent.parent_variant_id == variant_id)
            .all()
        )
