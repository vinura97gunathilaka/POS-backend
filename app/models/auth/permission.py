from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class Permission(Base, CompanyAuditMixin):
    __tablename__ = "permissions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    company = relationship("Company", back_populates="permissions")
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
