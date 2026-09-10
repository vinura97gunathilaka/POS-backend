"""
app.services.marketing_service
--------------------------------
Business logic for promotions, vouchers, and discount validation.

Responsibilities:
  - Promotion eligibility evaluation (date range, minimum spend)
  - Voucher code validation and redemption
  - Discount amount computation
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging import get_logger

logger = get_logger(__name__)


class MarketingService:
    """Promotions and voucher management business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def validate_voucher(self, code: str, company_id: int, sale_total: float) -> dict:
        """
        Validate a voucher code and return its discount value.
        Raises HTTP 400 if the voucher is invalid, expired, or already used.
        """
        from app.models.marketing import Voucher

        now = datetime.now(timezone.utc)
        voucher = (
            self.db.query(Voucher)
            .filter(
                Voucher.code == code,
                Voucher.company_id == company_id,
                Voucher.status == "active",
            )
            .first()
        )

        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired voucher code.",
            )

        if voucher.expiry_date and voucher.expiry_date < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This voucher has expired.",
            )

        if voucher.min_purchase_amount and sale_total < float(voucher.min_purchase_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Minimum purchase of {voucher.min_purchase_amount} required "
                    f"to use this voucher."
                ),
            )

        discount = float(voucher.discount_value or 0)
        logger.info("Voucher validated: code=%s discount=%.2f", code, discount)
        return {"voucher_id": voucher.id, "discount_value": discount, "type": voucher.discount_type}
