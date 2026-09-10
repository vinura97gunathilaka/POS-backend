"""
app.services.finance_service
------------------------------
Business logic for financial operations.

Responsibilities:
  - Shift open/close with cash reconciliation
  - Expense recording and category management
  - Bank account balance tracking
  - Cash drawer management
"""

from sqlalchemy.orm import Session
from app.core.logging import get_logger

logger = get_logger(__name__)


class FinanceService:
    """Financial and shift management business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate_shift_summary(self, shift_id: int) -> dict:
        """
        Aggregate sales, cash-in, cash-out, and expected closing balance
        for a given shift. Returns a summary dict.
        """
        from app.models.finance import Shift
        from app.models.sales import Sale, Payment

        shift = self.db.query(Shift).filter(Shift.id == shift_id).first()
        if not shift:
            return {}

        sales = self.db.query(Sale).filter(Sale.shift_id == shift_id).all()
        total_sales = sum(s.total_amount or 0 for s in sales)
        cash_sales = (
            self.db.query(Payment)
            .join(Sale, Payment.sale_id == Sale.id)
            .filter(Sale.shift_id == shift_id, Payment.payment_method == "cash")
            .all()
        )
        total_cash = sum(p.amount or 0 for p in cash_sales)

        return {
            "shift_id": shift_id,
            "total_sales": float(total_sales),
            "total_transactions": len(sales),
            "cash_collected": float(total_cash),
            "opening_balance": float(shift.opening_balance or 0),
            "expected_closing": float((shift.opening_balance or 0) + total_cash),
        }
