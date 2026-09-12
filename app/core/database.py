from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

def run_auto_migrations(target_engine):
    is_postgres = "postgresql" in str(target_engine.url)
    with target_engine.begin() as conn:
        if is_postgres:
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';"))
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(50) DEFAULT 'pro';"))
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMP;"))
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS max_users INTEGER;"))
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS max_branches INTEGER;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_id VARCHAR(50);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nic VARCHAR(50);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(500);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS has_system_access BOOLEAN DEFAULT TRUE;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;"))
            try:
                conn.execute(text("ALTER TABLE users ALTER COLUMN company_id DROP NOT NULL;"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL;"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE user_roles ALTER COLUMN company_id DROP NOT NULL;"))
            except Exception:
                pass

            # Audit logs table auto-migration
            audit_cols = [
                "branch_id INTEGER",
                "user_name VARCHAR(255)",
                "user_email VARCHAR(255)",
                "model_name VARCHAR(100)",
                "record_id VARCHAR(100)",
                "old_data JSON",
                "new_data JSON",
                "changes JSON",
                "user_agent VARCHAR(500)",
                "endpoint VARCHAR(255)",
                "http_method VARCHAR(20)",
                "status_code INTEGER"
            ]
            for acol in audit_cols:
                try:
                    conn.execute(text(f"ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS {acol};"))
                except Exception:
                    pass
            try:
                conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN company_id DROP NOT NULL;"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN action TYPE VARCHAR(100);"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN ip_address TYPE VARCHAR(100);"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE branches ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500);"))
            except Exception:
                pass
        else:
            for col_def in [
                "status VARCHAR(50) DEFAULT 'active'",
                "subscription_plan VARCHAR(50) DEFAULT 'pro'",
                "subscription_expires_at DATETIME",
                "max_users INTEGER",
                "max_branches INTEGER"
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE companies ADD COLUMN {col_def};"))
                except Exception:
                    pass
            for col_def in [
                "employee_id VARCHAR(50)",
                "nic VARCHAR(50)",
                "address VARCHAR(500)",
                "has_system_access BOOLEAN DEFAULT 1",
                "must_change_password BOOLEAN DEFAULT 0"
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_def};"))
                except Exception:
                    pass
            for acol in [
                "branch_id INTEGER",
                "user_name VARCHAR(255)",
                "user_email VARCHAR(255)",
                "model_name VARCHAR(100)",
                "record_id VARCHAR(100)",
                "old_data JSON",
                "new_data JSON",
                "changes JSON",
                "user_agent VARCHAR(500)",
                "endpoint VARCHAR(255)",
                "http_method VARCHAR(20)",
                "status_code INTEGER"
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {acol};"))
                except Exception:
                    pass

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Automatically register change data capture audit listeners for all sessions
from app.core.audit_listener import register_audit_listeners
register_audit_listeners(SessionLocal)

