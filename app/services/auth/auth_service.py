"""
app.services.auth_service
---------------------------
Business logic for authentication, token management, and initial admin setup.

Responsibilities:
  - Validate credentials and issue JWT access + refresh tokens
  - Refresh token rotation
  - Initial admin seed on first deployment
  - Password reset flow

Endpoint handlers in app.api.v1.endpoints.auth should delegate to this
service rather than implementing business logic inline.
"""

from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.repositories.user_repository import UserRepository, CompanyRepository, BranchRepository, RoleRepository
from app.models.auth import User

logger = get_logger(__name__)


class AuthService:
    """Handles all authentication and user session business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.company_repo = CompanyRepository(db)
        self.branch_repo = BranchRepository(db)
        self.role_repo = RoleRepository(db)

    # ------------------------------------------------------------------ #
    #  Login                                                               #
    # ------------------------------------------------------------------ #

    def authenticate(self, email: str, password: str) -> User:
        """
        Validate email/password and return the authenticated User.
        Raises HTTP 401 on failure.
        """
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt for email: %s", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account",
            )
        logger.info("User authenticated: user_id=%s", user.id)
        return user

    def issue_tokens(self, user_id: int) -> dict:
        """Generate and return a new access + refresh token pair."""
        return {
            "access_token": create_access_token(subject=user_id),
            "refresh_token": create_refresh_token(subject=user_id),
        }

    # ------------------------------------------------------------------ #
    #  Initial Admin Setup                                                 #
    # ------------------------------------------------------------------ #

    def setup_initial_admin(self) -> dict:
        """
        Seed the database with a default company, branch, and superadmin user
        if they don't already exist. Idempotent — safe to call multiple times.
        """
        from app.models.organization import Company, Branch, User

        # Check if already seeded
        existing = self.user_repo.get_by_email("admin@smartpos.com")
        if existing:
            logger.info("Initial setup already completed — skipping")
            return {"message": "Setup already completed. Admin user already exists."}

        # Create default company
        company = Company(
            name="Smart POS Corp",
            email="admin@smartpos.com",
            phone="+94000000000",
            status="active",
        )
        self.db.add(company)
        self.db.flush()

        # Create default branch
        branch = Branch(
            company_id=company.id,
            name="Main Branch",
            address="Head Office",
            status="active",
        )
        self.db.add(branch)
        self.db.flush()

        # Create superadmin user
        admin = User(
            company_id=company.id,
            email="admin@smartpos.com",
            full_name="Super Admin",
            hashed_password=get_password_hash("admin123"),
            is_superadmin=True,
            status="active",
        )
        self.db.add(admin)
        self.db.commit()

        logger.info(
            "Initial setup completed — company_id=%s, branch_id=%s, user_email=admin@smartpos.com",
            company.id,
            branch.id,
        )
        return {
            "message": "Initial setup complete. Login with admin@smartpos.com / admin123",
            "company_id": company.id,
            "branch_id": branch.id,
        }

