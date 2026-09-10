"""
app.services.analytics_service
--------------------------------
Business logic for reporting and analytics aggregations.

Responsibilities:
  - Daily / weekly / monthly sales summary generation
  - Top products and category performance
  - Branch comparison reports
  - Customer cohort and loyalty analytics
"""

from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Reporting and analytics aggregation business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_daily_sales_summary(
        self, company_id: int, branch_id: Optional[int] = None, target_date: Optional[date] = None
    ) -> dict:
        """
        Return total revenue, number of transactions, and average basket size
        for a given date (defaults to today).
        """
        from app.models.sales import Sale

        if target_date is None:
            target_date = date.today()

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        q = self.db.query(Sale).filter(
            Sale.company_id == company_id,
            Sale.created_at >= start,
            Sale.created_at <= end,
            Sale.status != "voided",
        )
        if branch_id:
            q = q.filter(Sale.branch_id == branch_id)

        sales = q.all()
        total_revenue = sum(s.total_amount or 0 for s in sales)
        transaction_count = len(sales)
        avg_basket = total_revenue / transaction_count if transaction_count else 0

        logger.debug(
            "Daily summary: date=%s company_id=%s revenue=%.2f txns=%s",
            target_date, company_id, total_revenue, transaction_count,
        )

        return {
            "date": str(target_date),
            "company_id": company_id,
            "branch_id": branch_id,
            "total_revenue": float(total_revenue),
            "transaction_count": transaction_count,
            "average_basket": round(avg_basket, 2),
        }
