import sys
import os

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Set env var if needed
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/smartpos"

from app.core.database import Base, engine
from app.models.sales import CSATFeedback

try:
    Base.metadata.create_all(bind=engine)
    print("Database migration successful: 'csat_feedbacks' table created/verified.")
except Exception as e:
    print(f"Database migration failed: {e}")
