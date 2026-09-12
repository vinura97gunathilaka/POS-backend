from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class RolePermission(Base, CompanyAuditMixin):
    __tablename__ = "role_permissions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
