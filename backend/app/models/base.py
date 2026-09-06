from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func

class AuditMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)  # User ID of creator
    updated_by = Column(Integer, nullable=True)  # User ID of updater
    status = Column(String(50), default="active", nullable=False) # active, inactive, archived, deleted

class CompanyAuditMixin(AuditMixin):
    # Relies on companies table. We declare the Column but handle foreign keys manually or dynamically to avoid circular references.
    company_id = Column(Integer, nullable=True)

class BranchAuditMixin(CompanyAuditMixin):
    branch_id = Column(Integer, nullable=True)
