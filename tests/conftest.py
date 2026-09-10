"""
tests/conftest.py
------------------
Shared pytest fixtures for the Smart POS test suite.

Fixtures available to all tests:
  - app         : FastAPI application instance
  - client      : Synchronous TestClient (no auth)
  - db          : In-memory SQLite session scoped per test function
  - auth_headers: Authorization headers with a seeded superadmin token
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import get_db
from app.models import Base
from app.core.security import get_password_hash, create_access_token

# --------------------------------------------------------------------------- #
#  In-memory SQLite engine for isolated test runs                             #
# --------------------------------------------------------------------------- #
TEST_DATABASE_URL = "sqlite:///./test_smartpos.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# --------------------------------------------------------------------------- #
#  Fixtures                                                                    #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session, drop them at the end."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db() -> Session:
    """Provide a transactional test DB session, rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """
    FastAPI TestClient with the real app, overriding get_db to use
    the per-test in-memory session.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_admin(db: Session):
    """Seed a superadmin user + company + branch and return the user object."""
    from app.models.organization import Company, Branch, User

    company = Company(name="Test Corp", email="test@corp.com", status="active")
    db.add(company)
    db.flush()

    branch = Branch(company_id=company.id, name="Test Branch", status="active")
    db.add(branch)
    db.flush()

    user = User(
        company_id=company.id,
        email="testadmin@smartpos.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("testpass123"),
        is_superadmin=True,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def auth_headers(seeded_admin) -> dict:
    """Return Bearer auth headers for the seeded admin user."""
    token = create_access_token(subject=seeded_admin.id)
    return {"Authorization": f"Bearer {token}"}

