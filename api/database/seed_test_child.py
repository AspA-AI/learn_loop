import psycopg2
import logging
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOCK_PARENT_ID = "00000000-0000-0000-0000-000000000000"

def seed_test_children():
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        return
    db_url = db_url.strip().strip('"').strip("'")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Seed Leo
        cur.execute("""
            INSERT INTO children (parent_id, name, age_level, learning_code, target_topic)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (learning_code) 
            DO UPDATE SET target_topic = EXCLUDED.target_topic;
        """, (MOCK_PARENT_ID, "Leo", 8, "LEO-782", "Photosynthesis"))

        # Seed Mia
        cur.execute("""
            INSERT INTO children (parent_id, name, age_level, learning_code, target_topic)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (learning_code) 
            DO UPDATE SET target_topic = EXCLUDED.target_topic;
        """, (MOCK_PARENT_ID, "Mia", 10, "MIA-290", "Mathematical Division"))

        conn.commit()
        logger.info("Test children 'Leo' (LEO-782) and 'Mia' (MIA-290) updated with new topics.")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    seed_test_children()
