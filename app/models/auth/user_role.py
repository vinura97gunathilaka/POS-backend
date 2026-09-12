from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class UserRole(Base, CompanyAuditMixin):
    __tablename__ = "user_roles"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
