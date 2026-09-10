"""
app.repositories.user_repository
----------------------------------
Data access layer for User, Role, Permission, Company, Branch entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.auth import User, Role, Permission
from app.models.organization import Company, Branch


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_active_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.email == email, User.status == "active")
            .first()
        )

    def get_by_company(self, company_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        return (
            self.db.query(User)
            .filter(User.company_id == company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session) -> None:
        super().__init__(Role, db)

    def get_by_name(self, name: str, company_id: int) -> Optional[Role]:
        return (
            self.db.query(Role)
            .filter(Role.name == name, Role.company_id == company_id)
            .first()
        )


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: Session) -> None:
        super().__init__(Permission, db)

    def get_by_code(self, code: str) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.code == code).first()


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session) -> None:
        super().__init__(Company, db)

    def get_by_name(self, name: str) -> Optional[Company]:
        return self.db.query(Company).filter(Company.name == name).first()


class BranchRepository(BaseRepository[Branch]):
    def __init__(self, db: Session) -> None:
        super().__init__(Branch, db)

    def get_by_company(self, company_id: int) -> List[Branch]:
        return (
            self.db.query(Branch)
            .filter(Branch.company_id == company_id, Branch.status == "active")
            .all()
        )

