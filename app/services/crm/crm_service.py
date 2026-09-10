"""
app.services.crm_service
--------------------------
Business logic for Customer Relationship Management.

Responsibilities:
  - Customer creation and deduplication (by phone/email)
  - Loyalty points calculation and redemption
  - Supplier management
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.repositories.crm_repository import (
    CustomerRepository,
    SupplierRepository,
    LoyaltyRuleRepository,
    LoyaltyTransactionRepository,
)

logger = get_logger(__name__)


class CRMService:
    """Customer and loyalty management business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.loyalty_rule_repo = LoyaltyRuleRepository(db)
        self.loyalty_tx_repo = LoyaltyTransactionRepository(db)

    def calculate_loyalty_points(self, company_id: int, sale_total: float) -> int:
        """
        Compute loyalty points to award for a given sale total.
        Returns 0 if no active loyalty rule exists.
        """
        rule = self.loyalty_rule_repo.get_active_by_company(company_id)
        if not rule or not rule.points_per_amount:
            return 0
        points = int(sale_total / rule.points_per_amount * rule.points_awarded)
        logger.debug("Loyalty points calculated: %s for sale_total=%.2f", points, sale_total)
        return points

    def redeem_points(self, customer_id: int, points: int, company_id: int) -> float:
        """
        Validate and compute monetary value of points being redeemed.
        Raises 400 if customer has insufficient balance.
        """
        rule = self.loyalty_rule_repo.get_active_by_company(company_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active loyalty program for this company.",
            )
        customer = self.customer_repo.get(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if (customer.loyalty_points or 0) < points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient loyalty points. Available: {customer.loyalty_points}",
            )
        redemption_value = points / rule.points_per_amount * rule.redemption_value
        return redemption_value
