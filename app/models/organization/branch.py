from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import CompanyAuditMixin

class Branch(Base, CompanyAuditMixin):
    __tablename__ = "branches"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    manager_id = Column(Integer, nullable=True)
    logo_url = Column(String(500), nullable=True)

    company = relationship("Company", back_populates="branches")
    users = relationship("User", secondary="user_branches", back_populates="branches")
