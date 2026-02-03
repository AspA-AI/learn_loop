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
    
    # Check if using pooler - warn user to use direct connection
    if 'pooler' in db_url.lower() or ':6543' in db_url:
        logger.warning("⚠️  You're using a connection pooler URL. For migrations, use the DIRECT connection string.")
        logger.warning("   Get it from: Supabase Dashboard → Settings → Database → Connection string → Direct connection")
        logger.warning("   It should use port 5432, not 6543")

    try:
        # Connect to the Supabase PostgreSQL database
        logger.info("Connecting to Supabase Database...")
        # Add connection timeout and keepalive settings
        conn = psycopg2.connect(
            db_url,
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
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

