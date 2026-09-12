from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin
from app.models.auth.user_branch import user_branches
from app.models.auth.user_role import UserRole

class User(Base, CompanyAuditMixin):
    __tablename__ = "users"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    employee_id = Column(String(50), nullable=True, index=True)
    nic = Column(String(50), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    has_system_access = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)

    company = relationship("Company", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    branches = relationship("Branch", secondary=user_branches, back_populates="users")

__all__ = ["User", "UserRole", "user_branches"]
