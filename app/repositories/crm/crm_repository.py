"""
app.repositories.crm_repository
----------------------------------
Data access layer for Customer, Supplier, Loyalty entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.crm import Customer, Supplier, LoyaltyRule, LoyaltyTransaction


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session) -> None:
        super().__init__(Customer, db)

    def get_by_phone(self, phone: str, company_id: int) -> Optional[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.phone == phone, Customer.company_id == company_id)
            .first()
        )

    def get_by_email(self, email: str, company_id: int) -> Optional[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.email == email, Customer.company_id == company_id)
            .first()
        )

    def search(self, company_id: int, query: str) -> List[Customer]:
        pattern = f"%{query}%"
        return (
            self.db.query(Customer)
            .filter(
                Customer.company_id == company_id,
                (Customer.name.ilike(pattern) | Customer.phone.ilike(pattern)),
            )
            .all()
        )

    def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 100
    ) -> List[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.company_id == company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, db: Session) -> None:
        super().__init__(Supplier, db)

    def get_by_company(
        self, company_id: int, skip: int = 0, limit: int = 100
    ) -> List[Supplier]:
        return (
            self.db.query(Supplier)
            .filter(Supplier.company_id == company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


class LoyaltyRuleRepository(BaseRepository[LoyaltyRule]):
    def __init__(self, db: Session) -> None:
        super().__init__(LoyaltyRule, db)

    def get_active_by_company(self, company_id: int) -> Optional[LoyaltyRule]:
        return (
            self.db.query(LoyaltyRule)
            .filter(LoyaltyRule.company_id == company_id, LoyaltyRule.status == "active")
            .first()
        )


class LoyaltyTransactionRepository(BaseRepository[LoyaltyTransaction]):
    def __init__(self, db: Session) -> None:
        super().__init__(LoyaltyTransaction, db)

    def get_by_customer(
        self, customer_id: int, skip: int = 0, limit: int = 50
    ) -> List[LoyaltyTransaction]:
        return (
            self.db.query(LoyaltyTransaction)
            .filter(LoyaltyTransaction.customer_id == customer_id)
            .order_by(LoyaltyTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
