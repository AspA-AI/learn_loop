import logging
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from core.config import settings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class WeaviateService:
    def __init__(self):
        self.client = None
        if not settings.WEAVIATE_URL:
            logger.info("WEAVIATE_URL not set. RAG features will be disabled.")
            return

        try:
            auth_credentials = Auth.api_key(settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None
            self.client = weaviate.connect_to_wcs(
                cluster_url=settings.WEAVIATE_URL,
                auth_credentials=auth_credentials
            )
            logger.info("Successfully connected to Weaviate.")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            self.client = None

    def retrieve_curriculum_context(self, concept: str, age_level: int) -> Optional[str]:
        if not self.client:
            return None
        
        if not self.client.is_live():
            logger.warning("Weaviate client is not live.")
            return None
            
        try:
            # v4 Querying
            educational_content = self.client.collections.get("EducationalContent")
            
            response = educational_content.query.near_text(
                query=concept,
                filters=Filter.by_property("age_range").equal(age_level),
                limit=1,
                return_properties=["explanation_text", "analogy_pool"]
            )
            
            if response.objects:
                obj = response.objects[0]
                props = obj.properties
                logger.info(f"Successfully retrieved curriculum context for {concept}")
                return f"Grounding Context: {props.get('explanation_text')}. Suggested Analogy: {props.get('analogy_pool')}"
        except Exception as e:
            logger.error(f"Weaviate retrieval error for {concept}: {e}")
            
        return None

    def close(self):
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate connection closed.")
            except Exception as e:
                logger.error(f"Error closing Weaviate connection: {e}")

weaviate_service = WeaviateService()

