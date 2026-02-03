import logging
import uuid
import random
import string
import warnings
import time
from datetime import datetime, timezone
from supabase import create_client, Client
from core.config import settings
from typing import List, Dict, Any, Optional
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

# Suppress Supabase deprecation warnings (they're harmless and will be fixed in future library versions)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='supabase')

def _is_schema_cache_missing_table(err: Exception) -> bool:
    """Supabase PostgREST returns PGRST205 when schema cache can't see a table yet."""
    try:
        if not isinstance(err, APIError):
            return False
        payload = err.args[0] if err.args else None
        return isinstance(payload, dict) and payload.get("code") == "PGRST205"
    except Exception:
        return False

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

    # --- Parent Management ---
    
    def create_parent(self, email: str, password_hash: str, name: Optional[str] = None, preferred_language: str = "English") -> Dict[str, Any]:
        """Create a new parent account"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Check if email already exists
            existing = self.client.table("parents").select("id").eq("email", email).execute()
            if existing.data:
                raise ValueError(f"Email address '{email}' is already registered")
            
            parent_data = {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "preferred_language": preferred_language
            }
            response = self.client.table("parents").insert(parent_data).execute()
            return response.data[0]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating parent: {e}")
            raise e

    def get_parent_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get parent by email"""
        if not self.client:
            return None
        try:
            response = self.client.table("parents").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching parent by email: {e}")
            return None

    def get_parent_by_id(self, parent_id: str) -> Optional[Dict[str, Any]]:
        """Get parent by ID"""
        if not self.client:
            return None
        try:
            response = self.client.table("parents").select("*").eq("id", parent_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching parent by id: {e}")
            return None

    def _generate_learning_code(self, name: str) -> str:
        """Generates a code like LEO-123"""
        prefix = name[:3].upper()
        suffix = ''.join(random.choices(string.digits, k=3))
        return f"{prefix}-{suffix}"

    # --- Child Management ---

    def create_child(self, parent_id: str, name: str, age_level: int, learning_style: Optional[str] = None, 
                     interests: Optional[List[str]] = None, reading_level: Optional[str] = None,
                     attention_span: Optional[str] = None, strengths: Optional[List[str]] = None,
                     learning_language: str = "English") -> Dict[str, Any]:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            learning_code = self._generate_learning_code(name)
            data = {
                "parent_id": parent_id,
                "name": name,
                "age_level": age_level,
                "learning_code": learning_code,
                "learning_language": learning_language
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

    def get_child_subjects(self, child_id: str) -> List[str]:
        """Get all unique subjects for a child"""
        if not self.client:
            return []
        try:
            response = self.client.table("child_topics").select("subject").eq("child_id", child_id).execute()
            subjects = list(set([t["subject"] for t in response.data]))
            return sorted(subjects) if subjects else []
        except Exception as e:
            logger.error(f"Error fetching child subjects: {e}")
            return []
    
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

    def add_child_topic(self, child_id: str, topic: str, subject: str = "General", set_as_active: bool = False) -> Dict[str, Any]:
        """Add a new topic to a child. If set_as_active is True, deactivates other topics."""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Check if topic already exists in this subject
            existing = self.client.table("child_topics").select("*").eq("child_id", child_id).eq("subject", subject).eq("topic", topic).execute()
            if existing.data:
                raise ValueError(f"Topic '{topic}' already exists in subject '{subject}' for this child.")
            
            # If setting as active, deactivate all other topics first
            if set_as_active:
                self.client.table("child_topics").update({"is_active": False}).eq("child_id", child_id).execute()
            
            # Insert new topic
            topic_data = {
                "child_id": child_id,
                "subject": subject,
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
                "storage_path": storage_path,  # Local file path (e.g., "curriculum/{parent_id}/{file_name}")
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

    def get_child_curriculum_files(self, child_id: str) -> List[Dict[str, Any]]:
        """Get all curriculum documents linked to a child"""
        if not self.client:
            logger.warning(f"⚠️ [CURRICULUM] Supabase client not available for child_id: {child_id}")
            return []
        try:
            logger.info(f"🔍 [CURRICULUM] Querying curriculum for child_id: {child_id}")
            # Get curriculum documents linked to this child
            response = self.client.table("child_curriculum").select("document_id, curriculum_documents(*)").eq("child_id", child_id).execute()
            
            logger.info(f"🔍 [CURRICULUM] Raw response data: {len(response.data) if response.data else 0} items")
            curriculum_files = []
            for item in response.data:
                if item.get("curriculum_documents"):
                    doc = item["curriculum_documents"]
                    curriculum_files.append({
                        "id": doc.get("id"),
                        "file_name": doc.get("file_name"),
                        "storage_path": doc.get("storage_path"),  # Local file path
                        "file_size": doc.get("file_size"),
                        "created_at": doc.get("created_at")
                    })
                    logger.info(f"✅ [CURRICULUM] Found curriculum: {doc.get('file_name')} (id: {doc.get('id')}, path: {doc.get('storage_path')})")
                else:
                    logger.warning(f"⚠️ [CURRICULUM] Item missing curriculum_documents: {item}")
            
            logger.info(f"📚 [CURRICULUM] Returning {len(curriculum_files)} curriculum files for child_id: {child_id}")
            return curriculum_files
        except Exception as e:
            logger.error(f"❌ [CURRICULUM] Error fetching child curriculum files for child_id {child_id}: {e}", exc_info=True)
            return []

    def remove_curriculum_for_child(self, child_id: str) -> List[str]:
        """
        Remove all curriculum documents for a specific child.
        Also deletes orphaned documents (documents not linked to any other children).
        Returns list of document IDs that were removed.
        """
        if not self.client:
            return []
        try:
            # Get all curriculum documents linked to this child
            response = self.client.table("child_curriculum").select("document_id").eq("child_id", child_id).execute()
            
            document_ids = [item["document_id"] for item in response.data]
            
            if not document_ids:
                return []
            
            # Remove links from child_curriculum table
            self.client.table("child_curriculum").delete().eq("child_id", child_id).execute()
            
            # Check which documents are orphaned (not linked to any other children)
            orphaned_doc_ids = []
            for doc_id in document_ids:
                # Check if this document is still linked to any other children
                remaining_links = self.client.table("child_curriculum").select("child_id").eq("document_id", doc_id).execute()
                if not remaining_links.data:
                    # Document is orphaned, delete it
                    orphaned_doc_ids.append(doc_id)
                    self.client.table("curriculum_documents").delete().eq("id", doc_id).execute()
                    logger.info(f"Deleted orphaned curriculum document: {doc_id}")
            
            return document_ids
        except Exception as e:
            logger.error(f"Error removing curriculum for child: {e}")
            raise e

    def get_curriculum_document_paths(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """Get storage paths for curriculum documents by their IDs"""
        if not self.client or not document_ids:
            return []
        try:
            response = self.client.table("curriculum_documents").select("id, storage_path").in_("id", document_ids).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching curriculum document paths: {e}")
            return []

    # --- Subject Document Management ---

    def get_subject_documents(self, child_id: str, subject: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific subject for a specific child"""
        if not self.client:
            return []
        try:
            response = self.client.table("subject_documents").select("*").eq("child_id", child_id).eq("subject", subject).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching subject documents: {e}")
            return []

    def get_subject_documents_by_parent(self, parent_id: str, subject: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific subject across all children of a parent"""
        if not self.client:
            return []
        try:
            # First get all children of this parent
            children_response = self.client.table("children").select("id").eq("parent_id", parent_id).execute()
            child_ids = [child["id"] for child in children_response.data]
            
            if not child_ids:
                return []
            
            # Get all documents for this subject from all children of this parent
            response = self.client.table("subject_documents").select("*").in_("child_id", child_ids).eq("subject", subject).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching subject documents by parent: {e}")
            return []

    def add_subject_document(self, child_id: str, subject: str, file_name: str, file_size: int, storage_path: Optional[str] = None, weaviate_collection_id: Optional[str] = None) -> Dict[str, Any]:
        """Add a document to a subject for a specific child (max 2 per child per subject)"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Check document count for this child and subject (max 2)
            existing = self.get_subject_documents(child_id, subject)
            if len(existing) >= 2:
                raise ValueError(f"Maximum 2 documents allowed per subject per child. Please remove an existing document first.")
            
            doc_data = {
                "child_id": child_id,
                "subject": subject,
                "file_name": file_name,
                "file_size": file_size,
                "storage_path": storage_path,
                "weaviate_collection_id": weaviate_collection_id
            }
            response = self.client.table("subject_documents").insert(doc_data).execute()
            return response.data[0]
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error adding subject document: {e}")
            raise e

    def remove_subject_document(self, child_id: str, document_id: str) -> bool:
        """Remove a subject document"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            self.client.table("subject_documents").delete().eq("id", document_id).eq("child_id", child_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error removing subject document: {e}")
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

    def end_session(self, session_id: str, evaluation_report: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None, academic_summary: Optional[str] = None, duration_seconds: Optional[int] = None):
        """End a session and save evaluation report, metrics and summary"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            # Get session to calculate duration if not provided
            session = self.get_session(session_id)
            ended_at = datetime.now(timezone.utc)
            
            # Calculate duration if not provided
            if duration_seconds is None:
                created_at_str = session.get("created_at")
                if created_at_str:
                    try:
                        # Parse ISO format timestamp
                        if isinstance(created_at_str, str):
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        else:
                            created_at = created_at_str
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        duration_seconds = int((ended_at - created_at).total_seconds())
                    except Exception as e:
                        logger.warning(f"Could not calculate duration from timestamps: {e}")
                        duration_seconds = None
            
            update_data = {
                "status": "completed",
                "evaluation_report": evaluation_report,
                "ended_at": ended_at.isoformat()
            }
            if metrics:
                update_data["metrics"] = metrics
            if academic_summary:
                update_data["academic_summary"] = academic_summary
            
            # Try to update with duration_seconds, but don't fail if column doesn't exist yet
            if duration_seconds is not None:
                try:
                    update_data["duration_seconds"] = duration_seconds
                    self.client.table("sessions").update(update_data).eq("id", session_id).execute()
                except APIError as e:
                    # If column doesn't exist (PGRST204), update without duration_seconds
                    if isinstance(e.args[0], dict) and e.args[0].get("code") == "PGRST204":
                        logger.warning(f"duration_seconds column not found in database. Please run migration: {e}")
                        update_data.pop("duration_seconds", None)
                        self.client.table("sessions").update(update_data).eq("id", session_id).execute()
                    else:
                        raise e
            else:
                self.client.table("sessions").update(update_data).eq("id", session_id).execute()
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            raise e

    # --- Formal Reports ---

    def create_formal_report(self, parent_id: str, child_id: str, report_type: str, start_date: str, end_date: str, content: str, metrics_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Save a generated formal report"""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            data = {
                "parent_id": parent_id,
                "child_id": child_id,
                "report_type": report_type,
                "start_date": start_date,
                "end_date": end_date,
                "content": content,
                "metrics_summary": metrics_summary
            }
            response = self.client.table("formal_reports").insert(data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving formal report: {e}")
            raise e

    def get_formal_reports(self, child_id: str) -> List[Dict[str, Any]]:
        """Get all formal reports for a child"""
        if not self.client:
            return []
        try:
            response = self.client.table("formal_reports").select("*").eq("child_id", child_id).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching formal reports: {e}")
            return []

    def get_formal_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific formal report"""
        if not self.client:
            return None
        try:
            response = self.client.table("formal_reports").select("*").eq("id", report_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching formal report: {e}")
            return None

    def get_sessions_by_date_range(self, child_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get all completed sessions for a child within a date range"""
        if not self.client:
            return []
        try:
            logger.info(f"Fetching sessions for child {child_id} from {start_date} to {end_date}")
            response = self.client.table("sessions").select("*")\
                .eq("child_id", child_id)\
                .eq("status", "completed")\
                .gte("created_at", start_date)\
                .lte("created_at", end_date)\
                .order("created_at", desc=True).execute()
            logger.info(f"Found {len(response.data)} completed sessions")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching sessions by date range: {e}")
            return []

    # --- Parent Advisor Chat + Guidance Notes ---

    def create_parent_advisor_chat(self, parent_id: str, child_id: str, focus_session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new per-child parent advisor chat session."""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        data = {"parent_id": parent_id, "child_id": child_id, "focus_session_id": focus_session_id}
        try:
            response = self.client.table("parent_advisor_chats").insert(data).execute()
            return response.data[0]
        except APIError as e:
            # PostgREST schema cache can lag briefly right after migrations. Retry a bit.
            if _is_schema_cache_missing_table(e):
                for delay in (0.5, 1.0, 2.0):
                    time.sleep(delay)
                    try:
                        response = self.client.table("parent_advisor_chats").insert(data).execute()
                        return response.data[0]
                    except APIError as e2:
                        if not _is_schema_cache_missing_table(e2):
                            raise
                raise RuntimeError(
                    "Supabase API schema cache hasn't picked up the new advisor-chat tables yet. "
                    "If you just ran migrations, wait ~30–60 seconds and try again. "
                    "If it persists, reload the schema cache in Supabase Dashboard (Settings → API → Reload schema)."
                )
            raise
        except Exception as e:
            logger.error(f"Error creating parent advisor chat: {e}")
            raise e

    def get_parent_advisor_chat(self, chat_id: str, parent_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by id (scoped to parent)."""
        if not self.client:
            return None
        try:
            response = self.client.table("parent_advisor_chats").select("*").eq("id", chat_id).eq("parent_id", parent_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching parent advisor chat: {e}")
            return None

    def update_parent_advisor_chat_focus(self, chat_id: str, parent_id: str, focus_session_id: Optional[str]) -> Dict[str, Any]:
        """Update focus_session_id for an existing advisor chat (scoped to parent)."""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            response = self.client.table("parent_advisor_chats") \
                .update({"focus_session_id": focus_session_id}) \
                .eq("id", chat_id) \
                .eq("parent_id", parent_id) \
                .execute()
            if not response.data:
                raise ValueError("Chat not found")
            return response.data[0]
        except APIError as e:
            if _is_schema_cache_missing_table(e):
                raise RuntimeError(
                    "Supabase schema cache missing 'parent_advisor_chats'. Apply migrations and reload schema cache."
                )
            raise
        except Exception as e:
            logger.error(f"Error updating parent advisor chat focus: {e}")
            raise e

    def add_parent_advisor_message(self, chat_id: str, role: str, content: str) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            data = {"chat_id": chat_id, "role": role, "content": content}
            response = self.client.table("parent_advisor_messages").insert(data).execute()
            return response.data[0]
        except APIError as e:
            if _is_schema_cache_missing_table(e):
                raise RuntimeError(
                    "Supabase schema cache missing 'parent_advisor_messages'. Apply migrations and reload schema cache."
                )
            raise
        except Exception as e:
            logger.error(f"Error adding parent advisor message: {e}")
            raise e

    def get_parent_advisor_messages(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            response = self.client.table("parent_advisor_messages")\
                .select("*")\
                .eq("chat_id", chat_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching parent advisor messages: {e}")
            return []

    def list_parent_advisor_chats(self, parent_id: str, child_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all advisor chats for a parent, optionally filtered by child_id. Returns chats with child info and message count."""
        if not self.client:
            return []
        try:
            query = self.client.table("parent_advisor_chats")\
                .select("*, children(id, name, age_level)")\
                .eq("parent_id", parent_id)\
                .order("created_at", desc=True)
            
            if child_id:
                query = query.eq("child_id", child_id)
            
            response = query.execute()
            
            # Get message counts for each chat
            chats_with_counts = []
            for chat in response.data:
                # Get message count by fetching all message IDs and counting
                try:
                    msg_response = self.client.table("parent_advisor_messages")\
                        .select("id")\
                        .eq("chat_id", chat["id"])\
                        .execute()
                    chat["message_count"] = len(msg_response.data) if msg_response.data else 0
                except Exception:
                    chat["message_count"] = 0
                chats_with_counts.append(chat)
            
            return chats_with_counts
        except Exception as e:
            logger.error(f"Error listing parent advisor chats: {e}")
            return []

    def add_parent_guidance_note(self, parent_id: str, child_id: str, note: str, source_chat_id: Optional[str] = None) -> Dict[str, Any]:
        """Append a new parent guidance note for a child (newest-first retrieval)."""
        if not self.client:
            raise Exception("Supabase client not initialized.")
        try:
            data = {"parent_id": parent_id, "child_id": child_id, "note": note, "source_chat_id": source_chat_id}
            response = self.client.table("parent_guidance_notes").insert(data).execute()
            return response.data[0]
        except APIError as e:
            if _is_schema_cache_missing_table(e):
                raise RuntimeError(
                    "Supabase schema cache missing 'parent_guidance_notes'. Apply migrations and reload schema cache."
                )
            raise
        except Exception as e:
            logger.error(f"Error adding parent guidance note: {e}")
            raise e

    def get_parent_guidance_notes(self, child_id: str, parent_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get newest guidance notes for a child. Optionally scope to parent."""
        if not self.client:
            return []
        try:
            q = self.client.table("parent_guidance_notes").select("*").eq("child_id", child_id)
            if parent_id:
                q = q.eq("parent_id", parent_id)
            response = q.order("created_at", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching parent guidance notes: {e}")
            return []

supabase_service = SupabaseService()
