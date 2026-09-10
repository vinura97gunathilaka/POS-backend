"""
app.repositories.inventory_repository
----------------------------------------
Data access layer for Inventory, StockTransaction, and StockTransfer entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.inventory import Inventory, StockTransaction, StockTransfer, StockTransferItem


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self, db: Session) -> None:
        super().__init__(Inventory, db)

    def get_by_variant_and_branch(
        self, variant_id: int, branch_id: int
    ) -> Optional[Inventory]:
        return (
            self.db.query(Inventory)
            .filter(
                Inventory.variant_id == variant_id,
                Inventory.branch_id == branch_id,
            )
            .first()
        )

    def get_by_branch(
        self, branch_id: int, skip: int = 0, limit: int = 200
    ) -> List[Inventory]:
        return (
            self.db.query(Inventory)
            .filter(Inventory.branch_id == branch_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_low_stock(self, branch_id: int) -> List[Inventory]:
        """Return inventory records where quantity_on_hand <= reorder_level."""
        return (
            self.db.query(Inventory)
            .filter(
                Inventory.branch_id == branch_id,
                Inventory.quantity_on_hand <= Inventory.reorder_level,
            )
            .all()
        )


class StockTransactionRepository(BaseRepository[StockTransaction]):
    def __init__(self, db: Session) -> None:
        super().__init__(StockTransaction, db)

    def get_by_branch(
        self, branch_id: int, skip: int = 0, limit: int = 100
    ) -> List[StockTransaction]:
        return (
            self.db.query(StockTransaction)
            .filter(StockTransaction.branch_id == branch_id)
            .order_by(StockTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_variant(self, variant_id: int) -> List[StockTransaction]:
        return (
            self.db.query(StockTransaction)
            .filter(StockTransaction.variant_id == variant_id)
            .order_by(StockTransaction.created_at.desc())
            .all()
        )


class StockTransferRepository(BaseRepository[StockTransfer]):
    def __init__(self, db: Session) -> None:
        super().__init__(StockTransfer, db)

    def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 50
    ) -> List[StockTransfer]:
        return (
            self.db.query(StockTransfer)
            .filter(StockTransfer.company_id == company_id)
            .order_by(StockTransfer.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pending_for_branch(self, branch_id: int) -> List[StockTransfer]:
        return (
            self.db.query(StockTransfer)
            .filter(
                StockTransfer.to_branch_id == branch_id,
                StockTransfer.status == "pending",
            )
            .all()
        )


class StockTransferItemRepository(BaseRepository[StockTransferItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(StockTransferItem, db)

    def get_by_transfer(self, transfer_id: int) -> List[StockTransferItem]:
        return (
            self.db.query(StockTransferItem)
            .filter(StockTransferItem.transfer_id == transfer_id)
            .all()
        )
