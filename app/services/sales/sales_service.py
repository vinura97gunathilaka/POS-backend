"""
app.services.sales_service
----------------------------
Core business logic for the Point-of-Sale transaction engine.

Responsibilities:
  - Invoice number generation
  - Cart total, tax, and discount calculation
  - Payment validation (overpayment / split-payment)
  - Stock deduction coordination (integrates InventoryService)
  - Loyalty point award coordination (integrates CRMService)
  - KDS broadcast coordination
  - CSAT feedback recording
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.repositories.sales_repository import SaleRepository, SaleItemRepository, PaymentRepository

logger = get_logger(__name__)


class SalesService:
    """POS transaction engine business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.sale_repo = SaleRepository(db)
        self.sale_item_repo = SaleItemRepository(db)
        self.payment_repo = PaymentRepository(db)

    def generate_invoice_number(self, branch_id: int, company_id: int) -> str:
        """
        Generate a unique, human-readable invoice number.
        Format: INV-{company_id:03d}-{branch_id:03d}-{sequence:06d}
        """
        count = self.sale_repo.count(
            filters=[
                self.sale_repo.model.company_id == company_id,
                self.sale_repo.model.branch_id == branch_id,
            ]
        )
        sequence = count + 1
        return f"INV-{company_id:03d}-{branch_id:03d}-{sequence:06d}"

    def calculate_totals(
        self,
        items: list,
        overall_discount: Decimal = Decimal("0"),
        discount_type: str = "flat",
    ) -> dict:
        """
        Compute subtotal, tax, discount, and grand total from a list of cart items.

        Args:
            items: List of dicts with keys: price, quantity, discount, tax_rate
            overall_discount: Order-level discount amount or percentage
            discount_type: 'flat' | 'percentage'

        Returns:
            dict with subtotal, item_discount, order_discount, tax_amount, total
        """
        subtotal = Decimal("0")
        item_discount_total = Decimal("0")
        tax_total = Decimal("0")

        for item in items:
            price = Decimal(str(item.get("price", 0)))
            qty = Decimal(str(item.get("quantity", 1)))
            item_disc = Decimal(str(item.get("discount", 0)))
            tax_rate = Decimal(str(item.get("tax_rate", 0)))

            line_subtotal = price * qty
            line_after_discount = line_subtotal - item_disc
            line_tax = line_after_discount * (tax_rate / Decimal("100"))

            subtotal += line_subtotal
            item_discount_total += item_disc
            tax_total += line_tax

        after_item_discounts = subtotal - item_discount_total

        if discount_type == "percentage":
            order_discount = after_item_discounts * (overall_discount / Decimal("100"))
        else:
            order_discount = overall_discount

        grand_total = after_item_discounts - order_discount + tax_total

        return {
            "subtotal": float(subtotal),
            "item_discount": float(item_discount_total),
            "order_discount": float(order_discount),
            "tax_amount": float(tax_total),
            "total": float(grand_total),
        }

    def validate_payments(self, payments: list, expected_total: float) -> None:
        """
        Validate that the payment list covers the sale total.
        Raises HTTP 400 if underpaid.
        """
        paid = sum(float(p.get("amount", 0)) for p in payments)
        if paid < expected_total - 0.01:  # 1-cent tolerance for float rounding
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Payment underpaid. Expected: {expected_total:.2f}, "
                    f"Received: {paid:.2f}"
                ),
            )
