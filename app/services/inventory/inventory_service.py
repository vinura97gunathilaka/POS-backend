"""
app.services.inventory_service
--------------------------------
Business logic for stock management.

Responsibilities:
  - Stock adjustment with transaction logging
  - Low-stock alert evaluation
  - Cross-branch stock transfer initiation and approval
  - BOM-based component deduction on sale
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.repositories.inventory_repository import (
    InventoryRepository,
    StockTransactionRepository,
    StockTransferRepository,
    StockTransferItemRepository,
)

logger = get_logger(__name__)


class InventoryService:
    """Stock management and transfer business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.stock_tx_repo = StockTransactionRepository(db)
        self.transfer_repo = StockTransferRepository(db)
        self.transfer_item_repo = StockTransferItemRepository(db)

    def get_stock(self, variant_id: int, branch_id: int) -> int:
        """Return current stock quantity for a variant at a branch (0 if not tracked)."""
        inv = self.inventory_repo.get_by_variant_and_branch(variant_id, branch_id)
        return int(inv.quantity_on_hand) if inv else 0

    def assert_sufficient_stock(
        self, variant_id: int, branch_id: int, qty_required: int
    ) -> None:
        """Raise 400 if stock is insufficient for the requested quantity."""
        available = self.get_stock(variant_id, branch_id)
        if available < qty_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for variant {variant_id}. "
                    f"Required: {qty_required}, Available: {available}"
                ),
            )

    def deduct_stock(
        self,
        variant_id: int,
        branch_id: int,
        quantity: int,
        reference_type: str = "sale",
        reference_id: Optional[int] = None,
        performed_by: Optional[int] = None,
    ) -> None:
        """
        Deduct stock from inventory and log a StockTransaction.
        Should be called inside the same DB transaction as the sale commit.
        """
        from app.models.inventory import Inventory, StockTransaction
        from datetime import datetime, timezone

        inv = self.inventory_repo.get_by_variant_and_branch(variant_id, branch_id)
        if inv is None:
            # Auto-create inventory record at 0 if it didn't exist
            inv = Inventory(
                variant_id=variant_id,
                branch_id=branch_id,
                quantity_on_hand=0,
                status="active",
            )
            self.db.add(inv)
            self.db.flush()

        inv.quantity_on_hand = (inv.quantity_on_hand or 0) - quantity

        tx = StockTransaction(
            variant_id=variant_id,
            branch_id=branch_id,
            quantity=-quantity,
            transaction_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
            status="active",
        )
        self.db.add(tx)
        logger.debug(
            "Stock deducted: variant_id=%s branch_id=%s qty=-%s ref=%s/%s",
            variant_id, branch_id, quantity, reference_type, reference_id,
        )
