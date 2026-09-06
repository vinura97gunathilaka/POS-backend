from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS preparation_status VARCHAR(50) DEFAULT 'none';"))
        conn.commit()
        print("Database migration successful: 'preparation_status' column added/verified on 'sales' table.")
except Exception as e:
    print(f"Database migration failed: {e}")
