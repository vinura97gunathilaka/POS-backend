from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class AuditLog(Base, CompanyAuditMixin):
    __tablename__ = "audit_logs"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True) # CREATE, UPDATE, DELETE, SOFT_DELETE, LOGIN, LOGIN_FAILED, LOGOUT, etc.
    model_name = Column(String(100), nullable=True, index=True) # Product, Sale, User, Customer, etc.
    record_id = Column(String(100), nullable=True, index=True)
    old_data = Column(JSON, nullable=True) # State before mutation
    new_data = Column(JSON, nullable=True) # State after mutation
    changes = Column(JSON, nullable=True) # Diff: {"field": {"old": ..., "new": ...}}
    details = Column(JSON, nullable=True) # Additional context, metadata, notes
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(255), nullable=True) # e.g. /api/v1/catalog/products
    http_method = Column(String(20), nullable=True) # POST, PUT, DELETE, etc.
    status_code = Column(Integer, nullable=True) # e.g. 200, 201, 400

    company = relationship("Company")
    branch = relationship("Branch")
    user = relationship("User")

    @property
    def display_user_name(self) -> str:
        if self.user_name:
            return self.user_name
        return self.user.name if self.user else "System"
