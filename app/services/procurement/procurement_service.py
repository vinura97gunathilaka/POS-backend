"""
app.services.procurement_service
----------------------------------
Business logic for purchase order management and goods receipt.

Responsibilities:
  - Purchase order creation and supplier validation
  - GRN (Goods Received Note) processing
  - Stock update on GRN approval (integrates InventoryService)
  - Purchase status lifecycle management (pending → received → complete)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.repositories.procurement_repository import PurchaseRepository, GRNRepository

logger = get_logger(__name__)


class ProcurementService:
    """Purchase order and goods receipt business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.purchase_repo = PurchaseRepository(db)
        self.grn_repo = GRNRepository(db)

    def approve_grn(self, grn_id: int, approved_by: int) -> None:
        """
        Approve a GRN and trigger stock updates for each received item.
        Idempotent — raises 400 if GRN is already approved.
        """
        from app.models.procurement import GRN, GRNItem
        from app.services.inventory_service import InventoryService

        grn = self.grn_repo.get_or_raise(grn_id, "GRN not found")

        if grn.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GRN is already approved.",
            )

        inventory_svc = InventoryService(self.db)
        items = self.db.query(GRNItem).filter(GRNItem.grn_id == grn_id).all()

        for item in items:
            from app.models.inventory import Inventory, StockTransaction

            inv = inventory_svc.inventory_repo.get_by_variant_and_branch(
                item.variant_id, grn.branch_id
            )
            if inv is None:
                inv = Inventory(
                    variant_id=item.variant_id,
                    branch_id=grn.branch_id,
                    quantity_on_hand=0,
                    status="active",
                )
                self.db.add(inv)
                self.db.flush()

            inv.quantity_on_hand = (inv.quantity_on_hand or 0) + item.quantity_received

            tx = StockTransaction(
                variant_id=item.variant_id,
                branch_id=grn.branch_id,
                quantity=item.quantity_received,
                transaction_type="grn",
                reference_id=grn_id,
                performed_by=approved_by,
                status="active",
            )
            self.db.add(tx)

        grn.status = "approved"
        self.db.commit()
        logger.info("GRN approved: grn_id=%s by user_id=%s", grn_id, approved_by)
