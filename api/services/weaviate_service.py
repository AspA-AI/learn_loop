import logging
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.classes.config import Property, DataType, Configure
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
            if not settings.WEAVIATE_API_KEY:
                logger.warning("WEAVIATE_API_KEY not set. Weaviate connection may fail or have limited functionality.")
            
            auth_credentials = Auth.api_key(settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None
            # Add OpenAI key to headers for vectorization
            headers = {
                "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
            } if settings.OPENAI_API_KEY else {}

            self.client = weaviate.connect_to_wcs(
                cluster_url=settings.WEAVIATE_URL,
                auth_credentials=auth_credentials,
                headers=headers
            )
            
            # Verify connection and authentication
            if self.client.is_live():
                logger.info("Successfully connected to Weaviate.")
                # Try a simple operation to verify authentication
                try:
                    # Just check if we can list collections (this will fail if auth is wrong)
                    _ = list(self.client.collections.list_all())
                    logger.info("Weaviate authentication verified.")
                except Exception as auth_check_error:
                    error_msg = str(auth_check_error).lower()
                    if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                        logger.error(f"⚠️ Weaviate authentication failed! Please verify WEAVIATE_API_KEY is correct. Error: {auth_check_error}")
                        logger.error("RAG features will be disabled until authentication is fixed.")
                        self.client = None
                    else:
                        logger.warning(f"Weaviate connection established but collection check failed: {auth_check_error}")
            else:
                logger.warning("Weaviate client is not live.")
                self.client = None
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                logger.error(f"⚠️ Failed to connect to Weaviate: Authentication error. Please check WEAVIATE_API_KEY. Error: {e}")
            else:
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
            # Check if collection exists first
            if not self.client.collections.exists("EducationalContent"):
                logger.debug(f"EducationalContent collection does not exist. Skipping curriculum context retrieval.")
                return None
            
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
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                logger.error(f"Weaviate authentication failed. Please check WEAVIATE_API_KEY. Error: {e}")
            elif "could not find class" in error_msg or "does not exist" in error_msg:
                logger.debug(f"Collection does not exist in Weaviate. This is expected if no documents have been uploaded yet.")
            else:
                logger.error(f"Weaviate retrieval error for {concept}: {e}")
            
        return None

    def store_subject_document_chunks(self, child_id: str, subject: str, topic: str, chunks: List[Dict[str, Any]], file_name: str) -> bool:
        """
        Store document chunks in Weaviate with subject/topic metadata.
        Creates/uses collection: SubjectDocuments
        Uses OpenAI embeddings (text2vec-openai) to vectorize the content.
        """
        if not self.client or not self.client.is_live():
            logger.warning("Weaviate client not available. Document chunks will not be stored.")
            return False
        
        try:
            collection_name = "SubjectDocuments"
            
            # Check if collection exists, create with OpenAI vectorizer if not
            # Handle authentication errors gracefully
            collection_exists = False
            try:
                collection_exists = self.client.collections.exists(collection_name)
            except Exception as auth_error:
                error_msg = str(auth_error).lower()
                if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                    logger.error(f"Weaviate authentication failed. Please check WEAVIATE_API_KEY in environment variables. Error: {auth_error}")
                    return False
                # If it's a different error (like collection doesn't exist), continue to create it
                logger.info(f"Collection '{collection_name}' check returned: {auth_error}. Will attempt to create.")
            
            if not collection_exists:
                logger.info(f"Creating collection '{collection_name}' with OpenAI vectorizer...")
                try:
                    self.client.collections.create(
                        name=collection_name,
                        vectorizer_config=Configure.Vectorizer.text2vec_openai(),  # Uses OpenAI to vectorize
                        properties=[
                            Property(name="content", data_type=DataType.TEXT),  # This will be vectorized
                            Property(name="child_id", data_type=DataType.TEXT),
                            Property(name="subject", data_type=DataType.TEXT),
                            Property(name="topic", data_type=DataType.TEXT),
                            Property(name="source_file", data_type=DataType.TEXT),
                            Property(name="chunk_index", data_type=DataType.INT),
                            Property(name="total_chunks", data_type=DataType.INT),
                        ]
                    )
                    logger.info(f"Successfully created '{collection_name}' collection with OpenAI vectorizer.")
                except Exception as create_error:
                    error_msg = str(create_error).lower()
                    if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                        logger.error(f"Weaviate authentication failed during collection creation. Please check WEAVIATE_API_KEY. Error: {create_error}")
                        return False
                    raise  # Re-raise if it's a different error
            
            collection = self.client.collections.get(collection_name)
            
            # Insert chunks with metadata
            with collection.batch.dynamic() as batch:
                for chunk_data in chunks:
                    batch.add_object(
                        properties={
                            "content": chunk_data["content"],
                            "child_id": child_id,
                            "subject": subject,
                            "topic": topic,
                            "source_file": file_name,
                            "chunk_index": chunk_data.get("chunk_index", 0),
                            "total_chunks": chunk_data.get("total_chunks", len(chunks))
                        }
                    )
            
            logger.info(f"Stored {len(chunks)} chunks for {subject}/{topic} from {file_name}")
            return True
        except Exception as e:
            logger.error(f"Error storing subject document chunks: {e}", exc_info=True)
            return False

    def delete_document_chunks(self, child_id: str, subject: str, file_name: str) -> bool:
        """
        Delete all chunks for a specific document from Weaviate.
        Used when replacing/updating a document.
        """
        if not self.client or not self.client.is_live():
            logger.warning("Weaviate client not available. Cannot delete chunks.")
            return False
        
        try:
            collection_name = "SubjectDocuments"
            
            # Check if collection exists
            try:
                if not self.client.collections.exists(collection_name):
                    logger.debug(f"Collection {collection_name} does not exist. Nothing to delete.")
                    return True  # Nothing to delete, consider it successful
            except Exception as auth_error:
                error_msg = str(auth_error).lower()
                if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                    logger.error(f"Weaviate authentication failed. Cannot delete chunks. Error: {auth_error}")
                    return False
                # Collection doesn't exist, nothing to delete
                return True
            
            collection = self.client.collections.get(collection_name)
            
            # Build filter to match this specific document
            filters = [
                Filter.by_property("child_id").equal(child_id),
                Filter.by_property("subject").equal(subject),
                Filter.by_property("source_file").equal(file_name)
            ]
            
            # Combine filters with AND
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            
            # Fetch objects matching the filter to get their UUIDs
            response = collection.query.fetch_objects(
                filters=combined_filter,
                limit=1000,  # Get all chunks for this document
                return_properties=[]  # We only need UUIDs
            )
            
            if response.objects:
                # Delete all matching objects
                uuids_to_delete = [obj.uuid for obj in response.objects]
                collection.data.delete_many(uuids=uuids_to_delete)
                logger.info(f"Deleted {len(uuids_to_delete)} chunks for document {file_name} (child_id: {child_id}, subject: {subject})")
                return True
            else:
                logger.debug(f"No chunks found to delete for document {file_name}")
                return True  # Nothing to delete, consider it successful
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                logger.error(f"Weaviate authentication failed. Cannot delete chunks. Error: {e}")
            else:
                logger.error(f"Error deleting document chunks: {e}", exc_info=True)
            return False

    def retrieve_all_topic_chunks(self, child_id: str, topic: str, subject: Optional[str] = None) -> Optional[str]:
        """
        Retrieve ALL relevant chunks for a topic at session start.
        Uses metadata filtering to get all chunks for the specific topic.
        Returns combined context string for the entire session.
        """
        if not self.client or not self.client.is_live():
            return None
        
        try:
            collection_name = "SubjectDocuments"
            
            # Check if collection exists first
            try:
                if not self.client.collections.exists(collection_name):
                    logger.debug(f"SubjectDocuments collection does not exist. No chunks available for topic {topic}.")
                    return None
            except Exception as auth_error:
                error_msg = str(auth_error).lower()
                if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                    logger.error(f"Weaviate authentication failed. Please check WEAVIATE_API_KEY. Error: {auth_error}")
                    return None
                # If collection doesn't exist, that's fine - just return None
                logger.debug(f"SubjectDocuments collection does not exist. No chunks available for topic {topic}.")
                return None
            
            collection = self.client.collections.get(collection_name)
            
            # Build filter: must match child_id and topic
            filters = [
                Filter.by_property("child_id").equal(child_id),
                Filter.by_property("topic").equal(topic)
            ]
            
            if subject:
                filters.append(Filter.by_property("subject").equal(subject))
            
            # Combine filters with AND
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            
            # Retrieve all chunks using metadata filters (exact match on topic)
            # We use fetch_objects instead of near_text since we want ALL chunks for this topic
            response = collection.query.fetch_objects(
                filters=combined_filter,
                limit=100,  # Adjust based on needs
                return_properties=["content", "source_file", "chunk_index"]
            )
            
            if response.objects:
                # Combine all chunks into context
                chunks = []
                for obj in response.objects:
                    props = obj.properties
                    chunks.append(f"[From {props.get('source_file', 'document')}]: {props.get('content', '')}")
                
                combined_context = "\n\n".join(chunks)
                logger.info(f"Retrieved {len(response.objects)} chunks for topic {topic}")
                return combined_context
            else:
                logger.info(f"No document chunks found for topic {topic}")
                return None
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                logger.error(f"Weaviate authentication failed. Please check WEAVIATE_API_KEY. Error: {e}")
            elif "could not find class" in error_msg or "does not exist" in error_msg:
                logger.debug(f"Collection does not exist in Weaviate. This is expected if no documents have been uploaded yet.")
            else:
                logger.error(f"Error retrieving topic chunks: {e}", exc_info=True)
            return None

    def close(self):
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate connection closed.")
            except Exception as e:
                logger.error(f"Error closing Weaviate connection: {e}")

weaviate_service = WeaviateService()

