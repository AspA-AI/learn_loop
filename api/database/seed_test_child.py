import psycopg2
import logging
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOCK_PARENT_ID = "00000000-0000-0000-0000-000000000000"

def seed_test_child():
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        return
    db_url = db_url.strip().strip('"').strip("'")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Insert a test child
        cur.execute("""
            INSERT INTO children (parent_id, name, age_level, learning_code, target_topic)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (learning_code) DO NOTHING;
        """, (MOCK_PARENT_ID, "Leo", 8, "LEO-782", "The Water Cycle"))

        conn.commit()
        logger.info("Test child 'Leo' seeded with code 'LEO-782'")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    seed_test_child()

