import weaviate
import logging
from weaviate.classes.config import Property, DataType, Configure
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_weaviate():
    if not settings.WEAVIATE_URL:
        logger.error("WEAVIATE_URL not found in .env")
        return

    client = weaviate.connect_to_wcs(
        cluster_url=settings.WEAVIATE_URL,
        auth_credentials=weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY)
    )

    try:
        # 1. Create EducationalContent Collection
        collection_name = "EducationalContent"
        
        if client.collections.exists(collection_name):
            logger.info(f"Collection '{collection_name}' already exists.")
        else:
            client.collections.create(
                name=collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_openai(), # Uses OpenAI to vectorize
                properties=[
                    Property(name="concept", data_type=DataType.TEXT),
                    Property(name="age_range", data_type=DataType.INT),
                    Property(name="explanation_text", data_type=DataType.TEXT),
                    Property(name="analogy_pool", data_type=DataType.TEXT),
                    Property(name="source_citation", data_type=DataType.TEXT),
                ]
            )
            logger.info(f"Successfully created '{collection_name}' collection.")

    except Exception as e:
        logger.error(f"Error initializing Weaviate: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    init_weaviate()

