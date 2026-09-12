from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import AuditMixin

class Company(Base, AuditMixin):
    __tablename__ = "companies"

    name = Column(String(255), nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    subscription_plan = Column(String(50), default="pro", nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    max_users = Column(Integer, nullable=True)
    max_branches = Column(Integer, nullable=True)
    settings = Column(JSON, default=dict, nullable=False)

    branches = relationship("Branch", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="company", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="company", cascade="all, delete-orphan")
