import logging
import uuid
import random
import string
from datetime import datetime, timezone
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

    def create_child(self, parent_id: str, name: str, age_level: int, learning_style: Optional[str] = None, 
                     interests: Optional[List[str]] = None, reading_level: Optional[str] = None,
                     attention_span: Optional[str] = None, strengths: Optional[List[str]] = None) -> Dict[str, Any]:
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
            # Add optional learning profile fields
            if learning_style:
                data["learning_style"] = learning_style
            if interests:
                data["interests"] = interests
            if reading_level:
                data["reading_level"] = reading_level
            if attention_span:
                data["attention_span"] = attention_span
            if strengths:
                data["strengths"] = strengths
            
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
    
    def get_child_by_id(self, child_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            response = self.client.table("children").select("*").eq("id", child_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching child by id: {e}")
            return None

    def update_child_topic(self, child_id: str, topic: str):
        """Legacy method - kept for backward compatibility. Use topic management methods instead."""
        if not self.client:
            return
        try:
            self.client.table("children").update({"target_topic": topic}).eq("id", child_id).execute()
        except Exception as e:
            logger.error(f"Error updating child topic: {e}")

    # --- Topic Management ---

    def get_child_topics(self, child_id: str) -> List[Dict[str, Any]]:
        """Get all topics for a child. If child_topics table is empty, migrates from target_topic."""
        if not self.client:
            return []
        try:
            response = self.client.table("child_topics").select("*").eq("child_id", child_id).order("created_at", desc=True).execute()
            
            # If no topics in child_topics, check if there's a target_topic to migrate
            if not response.data:
                child = self.get_child_by_id(child_id)
                if child and child.get("target_topic"):
                    # Migrate target_topic to child_topics
                    logger.info(f"Migrating target_topic '{child['target_topic']}' to child_topics for child {child_id}")
                    migrated_topic = self.add_child_topic(child_id, child["target_topic"], set_as_active=True)
                    return [migrated_topic]
            
            return response.data
        except Exception as e:
            logger.error(f"Error fetching child topics: {e}")
            return []

    def get_active_topic(self, child_id: str) -> Optional[Dict[str, Any]]:
        """Get the active topic for a child"""
        if not self.client:
            return None
        try:
            response = self.client.table("child_topics").select("*").eq("child_id", child_id).eq("is_active", True).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching active topic: {e}")
            return None

    def add_child_topic(self, child_id: str, topic: str, set_as_active: bool = False) -> Dict[str, Any]:
        """Add a new topic to a child. If set_as_active is True, deactivates other topics."""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Check if topic already exists
            existing = self.client.table("child_topics").select("*").eq("child_id", child_id).eq("topic", topic).execute()
            if existing.data:
                raise ValueError(f"Topic '{topic}' already exists for this child.")
            
            # If setting as active, deactivate all other topics first
            if set_as_active:
                self.client.table("child_topics").update({"is_active": False}).eq("child_id", child_id).execute()
            
            # Insert new topic
            topic_data = {
                "child_id": child_id,
                "topic": topic,
                "is_active": set_as_active
            }
            response = self.client.table("child_topics").insert(topic_data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error adding child topic: {e}")
            raise e

    def set_active_topic(self, child_id: str, topic_id: str) -> Dict[str, Any]:
        """Set a topic as active (deactivates all other topics for this child)"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Deactivate all topics for this child
            self.client.table("child_topics").update({"is_active": False}).eq("child_id", child_id).execute()
            
            # Activate the specified topic
            response = self.client.table("child_topics").update({"is_active": True, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", topic_id).eq("child_id", child_id).execute()
            
            if not response.data:
                raise ValueError(f"Topic not found or doesn't belong to this child.")
            
            # Also update target_topic in children table for backward compatibility
            active_topic = response.data[0]["topic"]
            self.client.table("children").update({"target_topic": active_topic}).eq("id", child_id).execute()
            
            return response.data[0]
        except Exception as e:
            logger.error(f"Error setting active topic: {e}")
            raise e

    def remove_child_topic(self, child_id: str, topic_id: str) -> bool:
        """Remove a topic from a child. Only allowed if topic has no sessions."""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Get the topic to check if it has sessions
            topic_response = self.client.table("child_topics").select("topic").eq("id", topic_id).eq("child_id", child_id).execute()
            if not topic_response.data:
                raise ValueError("Topic not found or doesn't belong to this child.")
            
            topic_name = topic_response.data[0]["topic"]
            
            # Check if topic has any sessions
            sessions_response = self.client.table("sessions").select("id").eq("child_id", child_id).eq("concept", topic_name).execute()
            if sessions_response.data:
                raise ValueError(f"Cannot remove topic '{topic_name}' because it has {len(sessions_response.data)} session(s). Topics with sessions cannot be removed to preserve history.")
            
            # If this was the active topic, we need to handle that
            topic_data = self.client.table("child_topics").select("is_active").eq("id", topic_id).execute()
            was_active = topic_data.data[0].get("is_active", False) if topic_data.data else False
            
            # Delete the topic
            self.client.table("child_topics").delete().eq("id", topic_id).eq("child_id", child_id).execute()
            
            # If it was active, set the most recent topic as active (or clear target_topic if no topics left)
            if was_active:
                remaining_topics = self.get_child_topics(child_id)
                if remaining_topics:
                    # Set the most recently created topic as active
                    self.set_active_topic(child_id, remaining_topics[0]["id"])
                else:
                    # No topics left, clear target_topic
                    self.client.table("children").update({"target_topic": None}).eq("id", child_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error removing child topic: {e}")
            raise e

    # --- Curriculum Management ---

    def upload_file_to_storage(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Upload a file to Supabase Storage"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Create bucket if it doesn't exist (this will fail silently if bucket exists)
            try:
                self.client.storage.create_bucket(bucket_name, options={"public": False})
            except:
                pass  # Bucket might already exist
            
            # Upload file - Supabase Python client expects file-like object or bytes
            from io import BytesIO
            file_obj = BytesIO(file_content)
            
            response = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_obj,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            return response
        except Exception as e:
            logger.error(f"Error uploading file to storage: {e}")
            raise e
    
    def get_file_from_storage(self, bucket_name: str, file_path: str) -> bytes:
        """Download a file from Supabase Storage"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            response = self.client.storage.from_(bucket_name).download(file_path)
            return response
        except Exception as e:
            logger.error(f"Error downloading file from storage: {e}")
            raise e

    def add_curriculum_document(self, parent_id: str, file_name: str, child_ids: List[str], storage_path: Optional[str] = None, file_size: Optional[int] = None) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # 1. Insert document metadata
            doc_data = {
                "parent_id": parent_id,
                "file_name": file_name,
                "storage_path": storage_path,  # Path in Supabase Storage
                "file_size": file_size  # Size in bytes
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

    # --- Parent Insights ---

    def get_sessions_for_parent(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for all children of a parent"""
        if not self.client:
            return []
        try:
            # Get all children for parent, then get their sessions
            children_response = self.client.table("children").select("id, name, learning_code").eq("parent_id", parent_id).execute()
            children_map = {c["id"]: c for c in children_response.data}
            child_ids = list(children_map.keys())
            
            if not child_ids:
                return []
            
            # Get all sessions for these children
            sessions_response = self.client.table("sessions").select("*").in_("child_id", child_ids).order("created_at", desc=True).execute()
            
            # Enrich sessions with child info
            for session in sessions_response.data:
                child_id = session["child_id"]
                if child_id in children_map:
                    session["child_name"] = children_map[child_id]["name"]
                    session["child_learning_code"] = children_map[child_id]["learning_code"]
            
            return sessions_response.data
        except Exception as e:
            logger.error(f"Error fetching sessions for parent: {e}")
            return []

    def get_interactions_with_states(self, session_ids: List[str]) -> List[Dict[str, Any]]:
        """Get all interactions with understanding states for given sessions"""
        if not self.client or not session_ids:
            return []
        try:
            response = self.client.table("interactions").select("*").in_("session_id", session_ids).order("created_at").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching interactions with states: {e}")
            return []

    def end_session(self, session_id: str, evaluation_report: Dict[str, Any]):
        """End a session and save evaluation report"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            import json
            self.client.table("sessions").update({
                "status": "completed",
                "evaluation_report": json.dumps(evaluation_report),
                "ended_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", session_id).execute()
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            raise e

supabase_service = SupabaseService()
