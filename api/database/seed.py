import logging
from services.supabase_service import supabase_service
from services.weaviate_service import weaviate_service
from models.schemas import AgeLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    logger.info("Starting data seeding...")

    # 1. Seed Weaviate with initial Curriculum/Analogy context
    if weaviate_service.client:
        try:
            collection = weaviate_service.client.collections.get("EducationalContent")
            
            sample_content = [
                {
                    "concept": "Gravity",
                    "age_range": 6,
                    "explanation_text": "Gravity is like an invisible hug from the Earth that keeps us from floating away.",
                    "analogy_pool": "An invisible piece of string tied to your shoes.",
                    "source_citation": "Internal Pedagogy Team"
                },
                {
                    "concept": "Photosynthesis",
                    "age_range": 8,
                    "explanation_text": "Plants use sunlight to turn air and water into food. It's like they are cooking with light!",
                    "analogy_pool": "A solar-powered kitchen inside a leaf.",
                    "source_citation": "Science Curriculum v1"
                },
                {
                    "concept": "Solar System",
                    "age_range": 10,
                    "explanation_text": "The Solar System is a collection of 8 planets and other objects orbiting the Sun due to its massive gravity.",
                    "analogy_pool": "A giant cosmic neighborhood where the Sun is the big house in the middle.",
                    "source_citation": "Standard Astronomy Intro"
                }
            ]

            for item in sample_content:
                collection.data.insert(properties=item)
            
            logger.info("Successfully seeded Weaviate EducationalContent.")
        except Exception as e:
            logger.error(f"Failed to seed Weaviate: {e}")
    else:
        logger.warning("Weaviate client not connected. Skipping Weaviate seeding.")

    # 2. Seed Supabase with a sample session (Optional)
    if supabase_service.client:
        try:
            session_id = supabase_service.create_session(8, "Seeded Test Concept")
            supabase_service.add_interaction(session_id, "assistant", "Hello! I am your learning assistant. Let's learn about something new today!")
            logger.info(f"Successfully created a sample session in Supabase: {session_id}")
        except Exception as e:
            logger.error(f"Failed to seed Supabase: {e}")
    else:
        logger.warning("Supabase client not connected. Skipping Supabase seeding.")

if __name__ == "__main__":
    seed_data()

