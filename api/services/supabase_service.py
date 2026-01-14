import logging
import uuid
import random
import string
from supabase import create_client, Client
from core.config import settings
from typing import List, Dict, Any, Optional
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase credentials missing. Database features will not work.")
                self.client = None
            else:
                self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def _generate_learning_code(self, name: str) -> str:
        """Generates a code like LEO-123"""
        prefix = name[:3].upper()
        suffix = ''.join(random.choices(string.digits, k=3))
        return f"{prefix}-{suffix}"

    # --- Child Management ---

    def create_child(self, parent_id: str, name: str, age_level: int) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            learning_code = self._generate_learning_code(name)
            data = {
                "parent_id": parent_id,
                "name": name,
                "age_level": age_level,
                "learning_code": learning_code
            }
            response = self.client.table("children").insert(data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating child: {e}")
            raise e

    def get_child_by_code(self, learning_code: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            response = self.client.table("children").select("*").eq("learning_code", learning_code.upper()).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching child by code: {e}")
            return None

    def update_child_topic(self, child_id: str, topic: str):
        if not self.client:
            return
        try:
            self.client.table("children").update({"target_topic": topic}).eq("id", child_id).execute()
        except Exception as e:
            logger.error(f"Error updating child topic: {e}")

    # --- Curriculum Management ---

    def add_curriculum_document(self, parent_id: str, file_name: str, child_ids: List[str]) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # 1. Insert document metadata
            doc_data = {
                "parent_id": parent_id,
                "file_name": file_name
            }
            doc_response = self.client.table("curriculum_documents").insert(doc_data).execute()
            doc_id = doc_response.data[0]["id"]

            # 2. Link to children
            if child_ids:
                links = [{"child_id": cid, "document_id": doc_id} for cid in child_ids]
                self.client.table("child_curriculum").insert(links).execute()

            return doc_response.data[0]
        except Exception as e:
            logger.error(f"Error adding curriculum document: {e}")
            raise e

    # --- Session Management ---

    def create_session(self, child_id: str, concept: str, age_level: int) -> str:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            session_id = str(uuid.uuid4())
            data = {
                "id": session_id,
                "child_id": child_id,
                "concept": concept,
                "age_level": age_level
            }
            self.client.table("sessions").insert(data).execute()
            return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise e

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            response = self.client.table("sessions").select("*").eq("id", session_id).execute()
            if not response.data:
                raise ValueError(f"Session {session_id} not found")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            raise e

    def add_interaction(self, session_id: str, role: str, content: str, understanding_state: Optional[str] = None):
        if not self.client:
            return
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "understanding_state": understanding_state
            }
            self.client.table("interactions").insert(data).execute()
        except Exception as e:
            logger.error(f"Error adding interaction: {e}")

    def get_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            response = self.client.table("interactions").select("*").eq("session_id", session_id).order("created_at").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching interactions: {e}")
            return []

supabase_service = SupabaseService()
