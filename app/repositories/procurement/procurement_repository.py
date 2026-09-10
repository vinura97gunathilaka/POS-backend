"""
app.repositories.procurement_repository
------------------------------------------
Data access layer for Purchase, PurchaseItem, GRN, and GRNItem entities.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.procurement import Purchase, PurchaseItem, GRN, GRNItem


class PurchaseRepository(BaseRepository[Purchase]):
    def __init__(self, db: Session) -> None:
        super().__init__(Purchase, db)

    def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 50
    ) -> List[Purchase]:
        return (
            self.db.query(Purchase)
            .filter(Purchase.company_id == company_id)
            .order_by(Purchase.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_supplier(self, supplier_id: int) -> List[Purchase]:
        return (
            self.db.query(Purchase)
            .filter(Purchase.supplier_id == supplier_id)
            .order_by(Purchase.created_at.desc())
            .all()
        )

    def get_pending(self, company_id: int) -> List[Purchase]:
        return (
            self.db.query(Purchase)
            .filter(
                Purchase.company_id == company_id,
                Purchase.status == "pending",
            )
            .all()
        )


class PurchaseItemRepository(BaseRepository[PurchaseItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(PurchaseItem, db)

    def get_by_purchase(self, purchase_id: int) -> List[PurchaseItem]:
        return (
            self.db.query(PurchaseItem)
            .filter(PurchaseItem.purchase_id == purchase_id)
            .all()
        )


class GRNRepository(BaseRepository[GRN]):
    def __init__(self, db: Session) -> None:
        super().__init__(GRN, db)

    def get_by_purchase(self, purchase_id: int) -> List[GRN]:
        return (
            self.db.query(GRN)
            .filter(GRN.purchase_id == purchase_id)
            .all()
        )

    def get_by_branch(
        self, branch_id: int, skip: int = 0, limit: int = 50
    ) -> List[GRN]:
        return (
            self.db.query(GRN)
            .filter(GRN.branch_id == branch_id)
            .order_by(GRN.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


class GRNItemRepository(BaseRepository[GRNItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(GRNItem, db)

    def get_by_grn(self, grn_id: int) -> List[GRNItem]:
        return (
            self.db.query(GRNItem)
            .filter(GRNItem.grn_id == grn_id)
            .all()
        )
