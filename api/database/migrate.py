import psycopg2
import logging
import os
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        logger.error("SUPABASE_DB_URL not found in .env. Migration aborted.")
        return

    # Clean the URL (remove quotes and spaces that might come from .env parsing)
    db_url = db_url.strip().strip('"').strip("'")

    try:
        # Connect to the Supabase PostgreSQL database
        logger.info("Connecting to Supabase Database...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Read the schema.sql file
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r") as f:
            sql = f.read()

        # Execute the SQL
        logger.info("Executing migration script...")
        cur.execute(sql)
        
        # Commit changes
        conn.commit()
        logger.info("Migration successful! Tables 'sessions' and 'interactions' created.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migrations()

