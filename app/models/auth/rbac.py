from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import AuditMixin, CompanyAuditMixin, BranchAuditMixin

# Association Table for User - Branches (Multi-branch assign)
user_branches = Table(
    "user_branches",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("branch_id", Integer, ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True)
)

class Company(Base, AuditMixin):
    __tablename__ = "companies"

    name = Column(String(255), nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    settings = Column(JSON, default=dict, nullable=False)

    branches = relationship("Branch", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="company", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="company", cascade="all, delete-orphan")

class Branch(Base, CompanyAuditMixin):
    __tablename__ = "branches"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    manager_id = Column(Integer, nullable=True) # Linked to user id

    company = relationship("Company", back_populates="branches")
    users = relationship("User", secondary=user_branches, back_populates="branches")

class Permission(Base, CompanyAuditMixin):
    __tablename__ = "permissions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(100), nullable=False) # e.g. "sales:create"
    description = Column(String(255), nullable=True)

    company = relationship("Company", back_populates="permissions")
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")

class Role(Base, CompanyAuditMixin):
    __tablename__ = "roles"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    company = relationship("Company", back_populates="roles")
    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")

class RolePermission(Base, CompanyAuditMixin):
    __tablename__ = "role_permissions"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

class User(Base, CompanyAuditMixin):
    __tablename__ = "users"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    is_superadmin = Column(Boolean, default=False, nullable=False)

    company = relationship("Company", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    branches = relationship("Branch", secondary=user_branches, back_populates="users")

class UserRole(Base, CompanyAuditMixin):
    __tablename__ = "user_roles"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
