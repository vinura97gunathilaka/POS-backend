import sys
sys.path.append(r"/app")

from app.core.database import engine
from sqlalchemy import text

try:
    print("Running migration to create product_variant_components table...")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_variant_components (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                deleted_at TIMESTAMP WITH TIME ZONE NULL,
                created_by INTEGER NULL,
                updated_by INTEGER NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                parent_variant_id INTEGER NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
                component_variant_id INTEGER NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT unique_parent_component UNIQUE (parent_variant_id, component_variant_id)
            );
        """))
        conn.commit()
    print("Migration executed successfully!")
except Exception as e:
    print(f"Migration failed: {e}")
    raise e
