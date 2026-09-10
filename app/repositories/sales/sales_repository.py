"""
app.repositories.sales_repository
------------------------------------
Data access layer for Sale, SaleItem, Payment, and CSATFeedback entities.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.sales import Sale, SaleItem, Payment, CSATFeedback


class SaleRepository(BaseRepository[Sale]):
    def __init__(self, db: Session) -> None:
        super().__init__(Sale, db)

    def get_by_invoice(self, invoice_number: str) -> Optional[Sale]:
        return (
            self.db.query(Sale)
            .filter(Sale.invoice_number == invoice_number)
            .first()
        )

    def get_by_branch(
        self, branch_id: int, skip: int = 0, limit: int = 50
    ) -> List[Sale]:
        return (
            self.db.query(Sale)
            .filter(Sale.branch_id == branch_id)
            .order_by(Sale.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 50
    ) -> List[Sale]:
        return (
            self.db.query(Sale)
            .filter(Sale.company_id == company_id)
            .order_by(Sale.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_customer(
        self, customer_id: int, skip: int = 0, limit: int = 50
    ) -> List[Sale]:
        return (
            self.db.query(Sale)
            .filter(Sale.customer_id == customer_id)
            .order_by(Sale.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_shift(self, shift_id: int) -> List[Sale]:
        return (
            self.db.query(Sale)
            .filter(Sale.shift_id == shift_id)
            .order_by(Sale.created_at.desc())
            .all()
        )


class SaleItemRepository(BaseRepository[SaleItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(SaleItem, db)

    def get_by_sale(self, sale_id: int) -> List[SaleItem]:
        return (
            self.db.query(SaleItem)
            .filter(SaleItem.sale_id == sale_id)
            .all()
        )


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session) -> None:
        super().__init__(Payment, db)

    def get_by_sale(self, sale_id: int) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.sale_id == sale_id)
            .all()
        )


class CSATFeedbackRepository(BaseRepository[CSATFeedback]):
    def __init__(self, db: Session) -> None:
        super().__init__(CSATFeedback, db)

    def get_by_sale(self, sale_id: int) -> Optional[CSATFeedback]:
        return (
            self.db.query(CSATFeedback)
            .filter(CSATFeedback.sale_id == sale_id)
            .first()
        )

    def get_by_branch(
        self, branch_id: int, skip: int = 0, limit: int = 100
    ) -> List[CSATFeedback]:
        return (
            self.db.query(CSATFeedback)
            .filter(CSATFeedback.branch_id == branch_id)
            .order_by(CSATFeedback.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
