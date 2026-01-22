import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
from models.schemas import (
    ChildProfile,
    ChildCreate,
    ChildUpdate,
    ParentInsight,
    ChildTopic,
    TopicCreate,
    ParentProfile,
    AdvisorChatStartRequest,
    AdvisorChatStartResponse,
    AdvisorChatMessageRequest,
    AdvisorChatMessageResponse,
    AdvisorChatFocusUpdateRequest,
    AdvisorChatFocusUpdateResponse,
)
from services.supabase_service import supabase_service
from services.weaviate_service import weaviate_service
from services.openai_service import openai_service
from agents.insight import insight_agent
from agents.advisor import advisor_agent, parent_guidance_summarizer
from utils.document_processor import process_document
from routes.auth import get_current_parent
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parent", tags=["parent"])

def verify_child_ownership(child_id: str, parent_id: str) -> dict:
    """Verify that a child belongs to the parent, returns child data if valid"""
    child = supabase_service.get_child_by_id(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    if str(child["parent_id"]) != parent_id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this child")
    return child

@router.get("/children", response_model=List[ChildProfile])
async def get_children(current_parent: dict = Depends(get_current_parent)):
    try:
        if not supabase_service.client:
            return []
        parent_id = str(current_parent["id"])
        response = supabase_service.client.table("children").select("*").eq("parent_id", parent_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching children: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch children.")

@router.post("/children", response_model=ChildProfile)
async def create_child(request: ChildCreate, current_parent: dict = Depends(get_current_parent)):
    try:
        parent_id = str(current_parent["id"])
        child = supabase_service.create_child(
            parent_id, 
            request.name, 
            request.age_level,
            learning_style=request.learning_style,
            interests=request.interests,
            reading_level=request.reading_level,
            attention_span=request.attention_span,
            strengths=request.strengths,
            learning_language=request.learning_language
        )
        return child
    except Exception as e:
        logger.error(f"Error creating child: {e}")
        raise HTTPException(status_code=500, detail="Failed to create child profile.")

@router.patch("/children/{child_id}", response_model=ChildProfile)
async def update_child(child_id: UUID, request: ChildUpdate, current_parent: dict = Depends(get_current_parent)):
    try:
        parent_id = str(current_parent["id"])
        
        # Verify the child belongs to this parent
        child = supabase_service.get_child_by_id(str(child_id))
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")
        if str(child["parent_id"]) != parent_id:
            raise HTTPException(status_code=403, detail="You don't have permission to update this child")
        
        update_data = request.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        response = supabase_service.client.table("children").update(update_data).eq("id", str(child_id)).eq("parent_id", parent_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Child not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating child: {e}")
        raise HTTPException(status_code=500, detail="Failed to update child profile.")

@router.post("/curriculum/upload")
async def upload_curriculum(
    file: UploadFile = File(...),
    child_ids: str = Form(...), # JSON string of UUIDs
    current_parent: dict = Depends(get_current_parent)
):
    """
    Upload curriculum file for selected children.
    If a child already has a curriculum, it will be replaced with the new one.
    Files are saved locally in learn_loop/curriculum/ until S3 bucket is available.
    """
    try:
        ids = json.loads(child_ids)
        
        # 1. Remove existing curriculum for each child (replace functionality)
        removed_files = []
        for child_id in ids:
            try:
                # Get existing curriculum documents for this child
                existing_curriculum = supabase_service.get_child_curriculum_files(child_id)
                
                if existing_curriculum:
                    # Remove database links
                    removed_doc_ids = supabase_service.remove_curriculum_for_child(child_id)
                    
                    # Get file paths for removed documents
                    doc_paths = supabase_service.get_curriculum_document_paths(removed_doc_ids)
                    
                    # Delete old files from local storage
                    for doc_path_info in doc_paths:
                        storage_path = doc_path_info.get("storage_path")
                        if storage_path:
                            file_path = Path(storage_path)
                            if file_path.exists():
                                try:
                                    file_path.unlink()
                                    removed_files.append(str(file_path))
                                    logger.info(f"Removed old curriculum file: {file_path}")
                                except Exception as e:
                                    logger.warning(f"Failed to delete old curriculum file {file_path}: {e}")
                    
                    logger.info(f"Replaced existing curriculum for child {child_id}")
            except Exception as e:
                logger.warning(f"Error removing existing curriculum for child {child_id}: {e}")
                # Continue with upload even if removal fails
        
        # 2. Read new file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # 3. Save new file locally in learn_loop/curriculum/{parent_id}/{file_name}
        parent_id = str(current_parent["id"])
        curriculum_dir = Path("curriculum") / parent_id
        curriculum_dir.mkdir(parents=True, exist_ok=True)
        
        local_file_path = curriculum_dir / file.filename
        
        # Write file to local storage
        with open(local_file_path, "wb") as f:
            f.write(file_content)
        
        # Store relative path for database (e.g., "curriculum/{parent_id}/{file_name}")
        storage_path = f"curriculum/{parent_id}/{file.filename}"
        
        # 4. Store new document metadata in database
        doc = supabase_service.add_curriculum_document(
            parent_id, 
            file.filename, 
            ids,
            storage_path=storage_path,  # Local file path
            file_size=file_size
        )
        
        logger.info(f"Curriculum file saved locally: {local_file_path}")
        
        return {
            "status": "success", 
            "document": doc, 
            "storage_path": storage_path,
            "local_path": str(local_file_path),
            "replaced": len(removed_files) > 0,
            "removed_files": removed_files
        }
    except Exception as e:
        logger.error(f"Error uploading curriculum: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload curriculum: {str(e)}")

@router.get("/curriculum")
async def get_curriculum(current_parent: dict = Depends(get_current_parent)):
    try:
        parent_id = str(current_parent["id"])
        response = supabase_service.client.table("curriculum_documents").select("*, children:child_curriculum(child_id)").eq("parent_id", parent_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching curriculum: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch curriculum.")

@router.delete("/curriculum/{document_id}")
async def remove_curriculum(document_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Remove a curriculum document and its associated files"""
    try:
        # Get document info to find file path
        if not supabase_service.client:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        parent_id = str(current_parent["id"])
        doc_response = supabase_service.client.table("curriculum_documents").select("*").eq("id", str(document_id)).eq("parent_id", parent_id).execute()
        
        if not doc_response.data:
            raise HTTPException(status_code=404, detail="Curriculum document not found")
        
        doc = doc_response.data[0]
        storage_path = doc.get("storage_path")
        
        # Delete file from local storage
        if storage_path:
            file_path = Path(storage_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"Deleted curriculum file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete curriculum file {file_path}: {e}")
        
        # Delete from database (cascade will remove child_curriculum links)
        supabase_service.client.table("curriculum_documents").delete().eq("id", str(document_id)).execute()
        
        return {"status": "success", "message": "Curriculum document removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing curriculum: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to remove curriculum: {str(e)}")

@router.get("/children/{child_id}/subjects")
async def get_child_subjects(child_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Get all unique subjects for a specific child"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        subjects = supabase_service.get_child_subjects(str(child_id))
        return {"child_id": str(child_id), "subjects": subjects}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching child subjects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch child subjects.")

@router.get("/children/{child_id}/topics", response_model=List[ChildTopic])
async def get_child_topics(child_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Get all topics for a specific child"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        topics = supabase_service.get_child_topics(str(child_id))
        return topics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching child topics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch child topics.")

@router.post("/children/{child_id}/topics", response_model=ChildTopic)
async def add_child_topic(child_id: UUID, request: TopicCreate, current_parent: dict = Depends(get_current_parent)):
    """Add a new topic to a child"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        topic = supabase_service.add_child_topic(
            str(child_id),
            request.topic,
            request.subject,
            set_as_active=request.set_as_active
        )
        return topic
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding child topic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add topic.")

@router.patch("/children/{child_id}/topics/{topic_id}/activate", response_model=ChildTopic)
async def activate_topic(child_id: UUID, topic_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Set a topic as active (deactivates all other topics for this child)"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        topic = supabase_service.set_active_topic(str(child_id), str(topic_id))
        return topic
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating topic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to activate topic.")

@router.delete("/children/{child_id}/topics/{topic_id}")
async def remove_child_topic(child_id: UUID, topic_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Remove a topic from a child. Only allowed if topic has no sessions."""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        success = supabase_service.remove_child_topic(str(child_id), str(topic_id))
        return {"success": success, "message": "Topic removed successfully."}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing child topic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove topic.")

# --- Formal Reporting Endpoints ---

@router.get("/children/{child_id}/reports/generate")
async def generate_report(
    child_id: str, 
    report_type: str = "monthly", # 'weekly', 'monthly', 'custom'
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_parent: dict = Depends(get_current_parent)
):
    try:
        parent_id = str(current_parent["id"])
        child = verify_child_ownership(child_id, parent_id)
        
        # Calculate date range if not provided
        if not end_date:
            # Use tomorrow's date to ensure today's sessions are included in 'lte'
            end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        if not start_date:
            if report_type == "weekly":
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            else: # monthly default
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # 1. Fetch all completed sessions in range
        sessions = supabase_service.get_sessions_by_date_range(child_id, start_date, end_date)
        
        if not sessions:
            raise HTTPException(status_code=404, detail="No completed sessions found for this period.")
        
        # 2. Fetch curriculum info
        curriculum = supabase_service.get_child_curriculum_files(child_id)
        curriculum_names = [c["file_name"] for c in curriculum] if curriculum else ["Standard Homeschool Curriculum"]

        # 3. Generate formal report using InsightAgent
        report_data = await insight_agent.generate_formal_periodic_report(
            child_info=child,
            parent_info=current_parent,
            sessions=sessions,
            curriculum_info=", ".join(curriculum_names),
            report_type=report_type
        )
        
        # 3. Save report to database
        saved_report = supabase_service.create_formal_report(
            parent_id=parent_id,
            child_id=child_id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            content=report_data["content"],
            metrics_summary=report_data["metrics_summary"]
        )
        
        return saved_report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate report.")

@router.get("/children/{child_id}/reports")
async def get_reports(child_id: str, current_parent: dict = Depends(get_current_parent)):
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(child_id, parent_id)
        return supabase_service.get_formal_reports(child_id)
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reports.")

@router.get("/reports/{report_id}/translate")
async def translate_report(
    report_id: str, 
    target_language: str, 
    current_parent: dict = Depends(get_current_parent)
):
    """Translate a formal report's narrative content on the fly"""
    try:
        parent_id = str(current_parent["id"])
        report = supabase_service.get_formal_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify ownership
        if str(report["parent_id"]) != parent_id:
            raise HTTPException(status_code=403, detail="Permission denied")
            
        # Parse content (handle both JSON and legacy plain text)
        content_obj = {}
        try:
            content_obj = json.loads(report["content"])
        except:
            content_obj = {"narrative": report["content"]}
            
        # Translate each part
        translated_obj = {}
        for key, text in content_obj.items():
            if text:
                translated_obj[key] = await insight_agent.translate_report(text, target_language)
            else:
                translated_obj[key] = text
                
        # Also translate the recommendation if it exists
        recommendation = report.get("recommendation")
        translated_recommendation = None
        if recommendation:
            translated_recommendation = await insight_agent.translate_report(recommendation, target_language)
            
        return {
            "id": report_id,
            "content": json.dumps(translated_obj),
            "recommendation": translated_recommendation,
            "target_language": target_language
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error translating report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to translate report.")

@router.get("/reports/{report_id}")
async def get_report_detail(report_id: str, current_parent: dict = Depends(get_current_parent)):
    try:
        parent_id = str(current_parent["id"])
        report = supabase_service.get_formal_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify ownership
        if str(report["parent_id"]) != parent_id:
            raise HTTPException(status_code=403, detail="Permission denied")
            
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report.")

@router.get("/children/{child_id}/subjects/{subject}/documents")
async def get_subject_documents(child_id: UUID, subject: str, current_parent: dict = Depends(get_current_parent)):
    """Get all documents for a specific subject"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        documents = supabase_service.get_subject_documents(str(child_id), subject)
        return {"child_id": str(child_id), "subject": subject, "documents": documents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subject documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch subject documents.")

@router.post("/children/{child_id}/subjects/{subject}/documents")
async def upload_subject_document(
    child_id: UUID,
    subject: str,
    topic: str = Form(...),
    file: UploadFile = File(...),
    current_parent: dict = Depends(get_current_parent)
):
    """
    Upload a document for a specific subject.
    Max 2 documents per child per subject, max 10MB per file.
    Each child can have their own documents since they may be at different grade levels.
    """
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        
        # 1. Validate file size (10MB = 10 * 1024 * 1024 bytes)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum of 10MB")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # 2. Check document count (max 2 per child per subject)
        existing_docs = supabase_service.get_subject_documents(str(child_id), subject)
        if len(existing_docs) >= 2:
            raise HTTPException(status_code=400, detail="Maximum 2 documents allowed per subject per child. Please remove an existing document first.")
        
        # 3. Process document (chunk, embed, store in Weaviate)
        try:
            chunks = process_document(file_content, file.filename)
            logger.info(f"Processed {file.filename}: {len(chunks)} chunks created")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # 4. Store chunks in Weaviate
        weaviate_success = weaviate_service.store_subject_document_chunks(
            child_id=str(child_id),
            subject=subject,
            topic=topic,
            chunks=chunks,
            file_name=file.filename
        )
        
        if not weaviate_success:
            logger.warning(f"Failed to store chunks in Weaviate for {file.filename}, but continuing...")
        
        # 5. Save metadata to database (file content already extracted and stored in Weaviate)
        # We don't need to store the original file since it's chunked and embedded in Weaviate
        doc = supabase_service.add_subject_document(
            child_id=str(child_id),
            subject=subject,
            file_name=file.filename,
            file_size=file_size,
            storage_path=None,  # Not storing original file, only metadata
            weaviate_collection_id="SubjectDocuments"
        )
        
        return {
            "success": True,
            "document": doc,
            "chunks_created": len(chunks),
            "message": f"Document uploaded and processed successfully. {len(chunks)} chunks created."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading subject document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.delete("/children/{child_id}/subjects/{subject}/documents/{document_id}")
async def remove_subject_document(child_id: UUID, subject: str, document_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Remove a document from a subject"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        
        # Get document info before deletion to remove from Weaviate
        documents = supabase_service.get_subject_documents(str(child_id), subject)
        doc_to_remove = next((d for d in documents if d["id"] == str(document_id)), None)
        
        if doc_to_remove:
            # TODO: Remove chunks from Weaviate by filtering on child_id, subject, and source_file
            # This would require a delete method in weaviate_service
            logger.info(f"Document {doc_to_remove['file_name']} metadata removed. Weaviate cleanup can be added if needed.")
        
        success = supabase_service.remove_subject_document(str(child_id), str(document_id))
        return {"success": success, "message": "Document removed successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing subject document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove document.")

@router.get("/children/{child_id}/evaluations")
async def get_child_evaluations(child_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Get all evaluation reports for a specific child"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        
        # Get all completed sessions for this child
        if not supabase_service.client:
            return {"child_id": str(child_id), "evaluations": []}
        
        sessions_response = supabase_service.client.table("sessions").select("*").eq("child_id", str(child_id)).eq("status", "completed").order("ended_at", desc=True).execute()
        
        evaluations = []
        for session in sessions_response.data:
            report = session.get("evaluation_report")
            if report:
                import json
                if isinstance(report, str):
                    report = json.loads(report)
                
                evaluations.append({
                    "session_id": session["id"],
                    "concept": session["concept"],
                    "ended_at": session.get("ended_at"),
                    "created_at": session.get("created_at"),
                    "evaluation_report": report
                })
        
        return {"child_id": str(child_id), "evaluations": evaluations}
    except Exception as e:
        logger.error(f"Error fetching child evaluations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch child evaluations.")

@router.get("/children/{child_id}/sessions")
async def get_child_sessions(child_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Get completed sessions for a specific child"""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        
        if not supabase_service.client:
            return {"child_id": str(child_id), "sessions": []}
        
        # Only fetch completed sessions for the history view
        sessions_response = supabase_service.client.table("sessions")\
            .select("*")\
            .eq("child_id", str(child_id))\
            .eq("status", "completed")\
            .order("created_at", desc=True)\
            .execute()
        
        sessions = []
        for session in sessions_response.data:
            sessions.append({
                "session_id": session["id"],
                "concept": session["concept"],
                "status": session.get("status", "active"),
                "created_at": session.get("created_at"),
                "ended_at": session.get("ended_at"),
                "evaluation_report": session.get("evaluation_report")
            })
        
        return {"child_id": str(child_id), "sessions": sessions}
    except Exception as e:
        logger.error(f"Error fetching child sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch child sessions.")

@router.get("/sessions/{session_id}/chat")
async def get_session_chat(session_id: UUID):
    """Get all chat interactions for a specific session"""
    try:
        # Get session info
        session = supabase_service.get_session(str(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        
        # Get all interactions for this session
        interactions = supabase_service.get_interactions(str(session_id))
        
        return {
            "session_id": str(session_id),
            "concept": session["concept"],
            "status": session.get("status", "active"),
            "created_at": session.get("created_at"),
            "ended_at": session.get("ended_at"),
            "interactions": [
                {
                    "role": i["role"],
                    "content": i["content"],
                    "transcribed_text": i.get("transcribed_text"),
                    "understanding_state": i.get("understanding_state"),
                    "created_at": i.get("created_at")
                }
                for i in interactions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch session chat.")

@router.patch("/profile", response_model=ParentProfile)
async def update_parent_profile(
    request: Dict[str, Any], 
    current_parent: dict = Depends(get_current_parent)
):
    """Update parent profile details (e.g. name, preferred_language)"""
    try:
        parent_id = str(current_parent["id"])
        
        # Only allow updating specific fields
        allowed_fields = ["name", "preferred_language"]
        update_data = {k: v for k, v in request.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
            
        response = supabase_service.client.table("parents").update(update_data).eq("id", parent_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Parent not found")
            
        parent = response.data[0]
        return ParentProfile(
            id=str(parent["id"]),
            email=parent["email"],
            name=parent.get("name"),
            preferred_language=parent.get("preferred_language", "English")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parent profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile.")

@router.get("/insights", response_model=Dict[str, Any])
async def get_insights(week: Optional[str] = Query(None), current_parent: dict = Depends(get_current_parent)):
    """Get aggregated insights and mastery stats for parent's children from stored reports"""
    try:
        # 1. Get all completed sessions with evaluation reports
        parent_id = str(current_parent["id"])
        sessions = supabase_service.get_sessions_for_parent(parent_id)
        completed_sessions = [s for s in sessions if s.get("status") == "completed" and s.get("evaluation_report")]
        
        if not completed_sessions:
            return {
                "summary": "No completed learning sessions found yet.",
                "children_stats": [],
                "overall_mastery": 0,
                "total_sessions": 0,
                "total_hours": 0,
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Complete a learning session to see progress!"]
            }
        
        # 2. Parse stored evaluation reports (no LLM call needed!)
        import json
        all_reports = []
        children_data = {}
        
        for session in completed_sessions:
            report = session.get("evaluation_report")
            if isinstance(report, str):
                report = json.loads(report)
            
            child_id = session["child_id"]
            child_name = session.get("child_name", "Unknown")
            
            if child_id not in children_data:
                children_data[child_id] = {
                    "child_id": child_id,
                    "name": child_name,
                    "sessions": [],
                    "mastery_scores": [],
                    "total_interactions": 0
                }
            
            children_data[child_id]["sessions"].append(session)
            children_data[child_id]["mastery_scores"].append(report.get("mastery_percent", 0))
            children_data[child_id]["total_interactions"] += report.get("total_interactions", 0)
            all_reports.append(report)
        
        # 3. Aggregate insights from stored reports
        all_achievements = []
        all_challenges = []
        all_next_steps = []
        
        for report in all_reports:
            all_achievements.extend(report.get("achievements", []))
            all_challenges.extend(report.get("challenges", []))
            all_next_steps.extend(report.get("recommended_next_steps", []))
        
        # 4. Calculate stats per child
        children_stats = []
        for child_id, data in children_data.items():
            avg_mastery = int(sum(data["mastery_scores"]) / len(data["mastery_scores"])) if data["mastery_scores"] else 0
            total_hours = round((data["total_interactions"] * 5) / 60, 1)
            
            children_stats.append({
                "child_id": str(child_id),
                "name": data["name"],
                "mastery_count": sum(1 for score in data["mastery_scores"] if score >= 80),  # Count high mastery sessions
                "mastery_percent": avg_mastery,
                "total_sessions": len(data["sessions"]),
                "total_hours": total_hours
            })
        
        # 5. Calculate overall stats
        overall_mastery = int(sum(r.get("mastery_percent", 0) for r in all_reports) / len(all_reports)) if all_reports else 0
        total_interactions = sum(r.get("total_interactions", 0) for r in all_reports)
        total_hours = round((total_interactions * 5) / 60, 1)
        
        # 6. Create summary from aggregated reports
        summary = f"Your children have completed {len(completed_sessions)} learning session(s). " \
                 f"Overall mastery across all sessions is {overall_mastery}%."
        
        return {
            "summary": summary,
            "children_stats": children_stats,
            "overall_mastery": overall_mastery,
            "total_sessions": len(completed_sessions),
            "total_hours": total_hours,
            "achievements": list(set(all_achievements))[:10],  # Deduplicate and limit
            "challenges": list(set(all_challenges))[:10],
            "recommended_next_steps": list(set(all_next_steps))[:5]
        }
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights.")


# --- Parent Advisor Chat ---

def _build_focus_session_context(session_id: str, child_id: str) -> str:
    """Build a bounded context string for a focus session (transcript + evaluation)."""
    try:
        session = supabase_service.get_session(session_id)
        if not session or str(session.get("child_id")) != str(child_id):
            return "(selected session not found for this child)"

        interactions = supabase_service.get_interactions(session_id)
        # Cap transcript to avoid runaway tokens
        transcript_lines: List[str] = []
        for i in interactions[-80:]:
            role = i.get("role", "user")
            content = (i.get("content") or "").strip()
            if not content:
                continue
            transcript_lines.append(f"{role}: {content}")
        transcript = "\n".join(transcript_lines)
        if len(transcript) > 12000:
            transcript = transcript[-12000:]

        evaluation = session.get("evaluation_report")
        metrics = session.get("metrics")
        academic_summary = session.get("academic_summary")

        return (
            f"Session ID: {session_id}\n"
            f"Concept: {session.get('concept')}\n"
            f"Status: {session.get('status')}\n"
            f"Created at: {session.get('created_at')}\n"
            f"Ended at: {session.get('ended_at')}\n\n"
            f"Academic summary (3 sentences): {academic_summary}\n\n"
            f"Metrics: {metrics}\n\n"
            f"Evaluation report JSON: {evaluation}\n\n"
            f"Transcript (most recent first bounded):\n{transcript}\n"
        )
    except Exception as e:
        logger.warning(f"Failed to build focus session context: {e}")
        return "(failed to load selected session context)"

def _build_child_overall_progress_context(child_id: str) -> str:
    """
    Bounded "overall progress" snapshot for the advisor agent.
    Uses the same underlying stored data we use for reports: sessions.metrics + sessions.academic_summary,
    and optionally the latest formal report.
    """
    try:
        if not supabase_service.client:
            return "(database unavailable)"

        # 1) Recent completed sessions with metrics + academic_summary
        sessions_resp = supabase_service.client.table("sessions") \
            .select("id, concept, created_at, ended_at, metrics, academic_summary") \
            .eq("child_id", str(child_id)) \
            .eq("status", "completed") \
            .order("created_at", desc=True) \
            .limit(8) \
            .execute()

        sessions = sessions_resp.data or []

        # Compute simple averages if metrics exist
        acc = conf = pers = expr = 0.0
        metric_count = 0
        session_lines: List[str] = []
        for s in sessions:
            metrics = s.get("metrics") or {}
            summary = (s.get("academic_summary") or "").strip()
            concept = s.get("concept")
            created_at = s.get("created_at")

            if isinstance(metrics, str):
                try:
                    metrics = json.loads(metrics)
                except Exception:
                    metrics = {}

            if isinstance(metrics, dict) and metrics:
                try:
                    acc += float(metrics.get("accuracy", 0) or 0)
                    conf += float(metrics.get("confidence", 0) or 0)
                    pers += float(metrics.get("persistence", 0) or 0)
                    expr += float(metrics.get("expression", 0) or 0)
                    metric_count += 1
                except Exception:
                    pass

            # Keep each line short and bounded
            if summary and len(summary) > 260:
                summary = summary[:260] + "…"
            session_lines.append(f"- {concept} ({created_at}): {summary or '(no academic summary saved)'} | metrics={metrics or '(none)'}")

        avg_block = "(no metrics yet)"
        if metric_count > 0:
            avg_block = {
                "accuracy_avg": round(acc / metric_count, 2),
                "confidence_avg": round(conf / metric_count, 2),
                "persistence_avg": round(pers / metric_count, 2),
                "expression_avg": round(expr / metric_count, 2),
                "sessions_counted": metric_count,
            }

        # 2) Latest formal report snapshot (optional, keep very small)
        latest_report_line = "(no formal reports yet)"
        try:
            reports = supabase_service.get_formal_reports(str(child_id)) or []
            if reports:
                r0 = reports[0]
                latest_report_line = f"Latest formal report: type={r0.get('report_type')} range={r0.get('start_date')}→{r0.get('end_date')} metrics_summary={r0.get('metrics_summary')}"
        except Exception:
            pass

        return (
            f"Recent completed sessions (max 8):\n" + ("\n".join(session_lines) if session_lines else "(none)") + "\n\n"
            f"Averaged metrics across recent sessions: {avg_block}\n\n"
            f"{latest_report_line}"
        )
    except Exception as e:
        logger.warning(f"Failed to build overall child progress context: {e}")
        return "(failed to load overall progress context)"

async def _detect_child_scope_mismatch(
    parent_message: str,
    selected_child_name: str,
    other_child_names: List[str],
    language: str = "English",
) -> Dict[str, Any]:
    """
    LLM-based guard to detect if the parent is discussing a different child than the selected one.
    Returns JSON: { scope: "selected"|"other"|"multiple"|"unclear", mentioned_children: [..], confidence: 0..1 }
    """
    # If there's only one child, there is no mismatch to detect.
    if not other_child_names:
        return {"scope": "selected", "mentioned_children": [], "confidence": 1.0}

    system = (
        "You are a strict classifier.\n"
        "Task: Determine whether the parent's message is about the currently selected child, a different child, multiple children, or unclear.\n"
        "Output MUST be valid JSON with keys: scope, mentioned_children, confidence.\n"
        "scope must be one of: selected, other, multiple, unclear.\n"
        "mentioned_children must be an array of names taken ONLY from the provided children list.\n"
        "confidence must be a number 0 to 1.\n"
        "Important:\n"
        "- Parents may refer indirectly (e.g., 'my other child', 'my daughter', 'the older one'). If it's clearly not the selected child, choose 'other'.\n"
        "- If the parent asks generally about 'my kids' or compares children, choose 'multiple'.\n"
        "- If the message is ambiguous (e.g., 'my child', 'my kid', 'my progress') and does NOT clearly reference another child, assume it refers to the selected child.\n"
        "- If you cannot tell AND there's no strong evidence it's about a different child, choose 'selected' (default to selected child to avoid unnecessary blocking).\n"
        "Do not include any extra keys.\n"
    )

    children_list = [selected_child_name] + other_child_names
    user = (
        f"Language: {language}\n"
        f"Selected child: {selected_child_name}\n"
        f"All children names: {children_list}\n\n"
        f"Parent message:\n{parent_message}\n"
    )

    try:
        txt = await openai_service.get_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        obj = json.loads(txt or "{}")
        scope = obj.get("scope", "unclear")
        mentioned = obj.get("mentioned_children", [])
        conf = obj.get("confidence", 0.0)
        if scope not in {"selected", "other", "multiple", "unclear"}:
            scope = "selected"
        if not isinstance(mentioned, list):
            mentioned = []
        mentioned = [m for m in mentioned if isinstance(m, str) and m in children_list]
        try:
            conf = float(conf)
        except Exception:
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        return {"scope": scope, "mentioned_children": mentioned, "confidence": conf}
    except Exception:
        # Fail open (don't block) if classifier fails
        return {"scope": "selected", "mentioned_children": [], "confidence": 0.0}

async def _detect_session_scope(
    parent_message: str,
    selected_focus_session_label: Optional[str],
    available_session_labels: List[str],
) -> Dict[str, Any]:
    """
    LLM-based helper that detects whether the parent is asking about a specific past session.
    - If no focus is selected and the message appears session-specific -> intent="needs_selection"
    - If focus is selected but message appears to refer to a different session -> intent="different_session"
    - Else -> intent="ok"
    Output JSON: { intent: "ok"|"needs_selection"|"different_session"|"unclear", confidence: 0..1 }
    """
    system = (
        "You are a strict classifier.\n"
        "Task: Determine whether the parent message is about a specific session (by date/time/that previous chat),\n"
        "and whether it matches the currently selected focus session.\n"
        "Output MUST be valid JSON with keys: intent, confidence.\n"
        "intent must be one of: ok, needs_selection, different_session, unclear.\n"
        "confidence must be a number 0 to 1.\n"
        "Rules:\n"
        "- If the parent says 'in that session', 'on that day', 'the session on Jan ...', or references a past conversation, it's session-specific.\n"
        "- If no focus session is selected and it's session-specific -> needs_selection.\n"
        "- If a focus session is selected and the message indicates a different session than the selected label -> different_session.\n"
        "- If the message is general progress ('my kid's progress') -> ok.\n"
        "Do not include any extra keys.\n"
    )

    user = (
        f"Selected focus session label (or null): {selected_focus_session_label}\n"
        f"Available session labels (for reference): {available_session_labels}\n\n"
        f"Parent message:\n{parent_message}\n"
    )

    try:
        txt = await openai_service.get_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=120,
            response_format={"type": "json_object"},
        )
        obj = json.loads(txt or "{}")
        intent = obj.get("intent", "unclear")
        conf = obj.get("confidence", 0.0)
        if intent not in {"ok", "needs_selection", "different_session", "unclear"}:
            intent = "unclear"
        try:
            conf = float(conf)
        except Exception:
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        return {"intent": intent, "confidence": conf}
    except Exception:
        return {"intent": "ok", "confidence": 0.0}


@router.post("/advisor/start", response_model=AdvisorChatStartResponse)
async def start_advisor_chat(request: AdvisorChatStartRequest, current_parent: dict = Depends(get_current_parent)):
    """Start a new per-child advisor chat. Optionally bind it to a focus session."""
    try:
        parent_id = str(current_parent["id"])
        child = verify_child_ownership(str(request.child_id), parent_id)

        chat = supabase_service.create_parent_advisor_chat(
            parent_id=parent_id,
            child_id=str(request.child_id),
            focus_session_id=str(request.focus_session_id) if request.focus_session_id else None,
        )

        # Seed with a short assistant greeting message (stored + returned)
        greeting = (
            f"Hi! I’m your Advisor Agent for {child.get('name','your child')}. "
            "What would you like to discuss about your child today?"
        )
        supabase_service.add_parent_advisor_message(str(chat["id"]), "assistant", greeting)

        messages = supabase_service.get_parent_advisor_messages(str(chat["id"]), limit=50)
        return AdvisorChatStartResponse(
            chat_id=UUID(str(chat["id"])),
            child_id=UUID(str(request.child_id)),
            focus_session_id=UUID(str(request.focus_session_id)) if request.focus_session_id else None,
            messages=messages,
        )
    except HTTPException:
        raise
    except RuntimeError as e:
        # e.g. missing table due to migrations not run
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting advisor chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start advisor chat.")


@router.get("/advisor/{chat_id}")
async def get_advisor_chat(chat_id: UUID, current_parent: dict = Depends(get_current_parent)):
    """Fetch advisor chat history (scoped to current parent)."""
    try:
        parent_id = str(current_parent["id"])
        chat = supabase_service.get_parent_advisor_chat(str(chat_id), parent_id=parent_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        messages = supabase_service.get_parent_advisor_messages(str(chat_id), limit=80)
        return {"chat": chat, "messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching advisor chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch advisor chat.")

@router.patch("/advisor/{chat_id}/focus", response_model=AdvisorChatFocusUpdateResponse)
async def update_advisor_chat_focus(chat_id: UUID, request: AdvisorChatFocusUpdateRequest, current_parent: dict = Depends(get_current_parent)):
    """
    Update the focus session for an existing advisor chat (same child, same chat).
    This keeps chat continuity while allowing the agent to use the newly selected session as context.
    """
    try:
        parent_id = str(current_parent["id"])
        chat = supabase_service.get_parent_advisor_chat(str(chat_id), parent_id=parent_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Verify the chat's child belongs to this parent
        verify_child_ownership(str(chat["child_id"]), parent_id)

        updated = supabase_service.update_parent_advisor_chat_focus(
            chat_id=str(chat_id),
            parent_id=parent_id,
            focus_session_id=str(request.focus_session_id) if request.focus_session_id else None,
        )

        return AdvisorChatFocusUpdateResponse(
            chat_id=UUID(str(updated["id"])),
            focus_session_id=UUID(str(updated["focus_session_id"])) if updated.get("focus_session_id") else None,
        )
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating advisor chat focus: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update chat focus.")


@router.post("/advisor/{chat_id}/message", response_model=AdvisorChatMessageResponse)
async def send_advisor_message(chat_id: UUID, request: AdvisorChatMessageRequest, current_parent: dict = Depends(get_current_parent)):
    """Send a message to the advisor agent within an existing per-child chat."""
    try:
        parent_id = str(current_parent["id"])
        chat = supabase_service.get_parent_advisor_chat(str(chat_id), parent_id=parent_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Verify child ownership (chat is per-child)
        child = verify_child_ownership(str(chat["child_id"]), parent_id)

        language = current_parent.get("preferred_language", "English")

        # Persist parent message
        supabase_service.add_parent_advisor_message(str(chat_id), "user", request.message)

        # Load history (bounded)
        db_messages = supabase_service.get_parent_advisor_messages(str(chat_id), limit=80)
        chat_history = [{"role": m["role"], "content": m["content"]} for m in db_messages if m.get("role") and m.get("content")]

        # --- Child-scope guard (LLM-based) ---
        # If parent appears to be talking about a different child, do not continue the conversation in the wrong scope.
        other_child_names: List[str] = []
        try:
            if supabase_service.client:
                children_resp = supabase_service.client.table("children").select("id, name").eq("parent_id", parent_id).execute()
                for c in (children_resp.data or []):
                    if str(c.get("id")) != str(child.get("id")) and c.get("name"):
                        other_child_names.append(str(c.get("name")))
        except Exception:
            other_child_names = []

        scope_check = await _detect_child_scope_mismatch(
            parent_message=request.message,
            selected_child_name=child.get("name", "this child"),
            other_child_names=other_child_names,
            language=language,
        )

        # Only block if the classifier is confident. Otherwise, proceed in selected-child context.
        scope = scope_check.get("scope")
        confidence = float(scope_check.get("confidence") or 0.0)
        if scope in {"other", "multiple"} and confidence >= 0.75:
            selected_name = child.get("name", "this child")
            mentioned = scope_check.get("mentioned_children") or []
            target = mentioned[0] if mentioned else "your other child"
            warning = (
                f"This chat is currently about {selected_name}. "
                f"If you want to discuss {target}, please select them from the left sidebar so I can switch context."
            )
            # Persist assistant warning and return without calling AdvisorAgent or summarizer
            supabase_service.add_parent_advisor_message(str(chat_id), "assistant", warning)
            return AdvisorChatMessageResponse(
                chat_id=UUID(str(chat_id)),
                assistant_message=warning,
                appended_notes=[],
            )

        # Guidance notes (bounded newest-first)
        notes_rows = supabase_service.get_parent_guidance_notes(child_id=str(child["id"]), parent_id=parent_id, limit=8)
        guidance_notes = [n.get("note") for n in notes_rows if n.get("note")]

        # Optional focus session context
        focus_session_id = chat.get("focus_session_id")
        focus_context = _build_focus_session_context(str(focus_session_id), str(child["id"])) if focus_session_id else None

        # --- Session-scope guard (LLM-based) ---
        # If the parent is asking about a specific session but hasn't selected one, prompt them to select.
        # If they seem to be referring to a different session than the selected one, remind them to switch.
        available_session_labels: List[str] = []
        selected_label: Optional[str] = None
        try:
            if supabase_service.client:
                sess_resp = supabase_service.client.table("sessions") \
                    .select("id, concept, created_at") \
                    .eq("child_id", str(child["id"])) \
                    .eq("status", "completed") \
                    .order("created_at", desc=True) \
                    .limit(12) \
                    .execute()
                for s in (sess_resp.data or []):
                    label = f"{s.get('created_at')} • {s.get('concept')} • {str(s.get('id'))[:8]}"
                    available_session_labels.append(label)
                    if focus_session_id and str(s.get("id")) == str(focus_session_id):
                        selected_label = label
        except Exception:
            available_session_labels = []
            selected_label = None

        session_check = await _detect_session_scope(
            parent_message=request.message,
            selected_focus_session_label=selected_label if focus_session_id else None,
            available_session_labels=available_session_labels,
        )

        if session_check.get("intent") == "needs_selection" and float(session_check.get("confidence") or 0.0) >= 0.75:
            prompt_msg = (
                f"To discuss a specific past session for {child.get('name','your child')}, "
                "please select the session date from the left sidebar first so I can load it as context."
            )
            supabase_service.add_parent_advisor_message(str(chat_id), "assistant", prompt_msg)
            return AdvisorChatMessageResponse(
                chat_id=UUID(str(chat_id)),
                assistant_message=prompt_msg,
                appended_notes=[],
            )

        if session_check.get("intent") == "different_session" and float(session_check.get("confidence") or 0.0) >= 0.75 and selected_label:
            remind = (
                f"Right now I’m using the selected session ({selected_label}). "
                "If you want to discuss a different session, please pick that session from the left sidebar so I can switch context."
            )
            supabase_service.add_parent_advisor_message(str(chat_id), "assistant", remind)
            return AdvisorChatMessageResponse(
                chat_id=UUID(str(chat_id)),
                assistant_message=remind,
                appended_notes=[],
            )

        # Build learning profile dict (do not ask parent to restate)
        learning_profile = {
            "learning_style": child.get("learning_style"),
            "interests": child.get("interests"),
            "reading_level": child.get("reading_level"),
            "attention_span": child.get("attention_span"),
            "strengths": child.get("strengths"),
        }
        if not any(v for v in learning_profile.values()):
            learning_profile = None

        assistant_message = await advisor_agent.respond(
            parent_name=current_parent.get("name"),
            child_name=child.get("name", "Child"),
            child_age=child.get("age_level"),
            child_learning_profile=learning_profile,
            guidance_notes=guidance_notes,
            child_overall_progress_context=_build_child_overall_progress_context(str(child["id"])),
            focus_session_context=focus_context,
            chat_history=chat_history,
            parent_message=request.message,
            language=language,
        )

        # Persist assistant message
        supabase_service.add_parent_advisor_message(str(chat_id), "assistant", assistant_message)

        # Summarize actionable notes from recent chat and append
        recent_for_summary = chat_history[-12:] + [{"role": "assistant", "content": assistant_message}]
        extracted = await parent_guidance_summarizer.extract_notes(
            child_name=child.get("name", "Child"),
            recent_chat=recent_for_summary,
            language=language,
        )

        appended_notes: List[str] = []
        for note in extracted:
            try:
                supabase_service.add_parent_guidance_note(
                    parent_id=parent_id,
                    child_id=str(child["id"]),
                    note=note,
                    source_chat_id=str(chat_id),
                )
                appended_notes.append(note)
            except Exception as e:
                logger.warning(f"Failed to persist guidance note: {e}")

        return AdvisorChatMessageResponse(
            chat_id=UUID(str(chat_id)),
            assistant_message=assistant_message,
            appended_notes=appended_notes,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending advisor message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send advisor message.")


@router.get("/children/{child_id}/guidance-notes")
async def get_child_guidance_notes(child_id: UUID, limit: int = Query(10, ge=1, le=50), current_parent: dict = Depends(get_current_parent)):
    """Get newest parent guidance notes for a child (for UI display / debugging)."""
    try:
        parent_id = str(current_parent["id"])
        verify_child_ownership(str(child_id), parent_id)
        notes = supabase_service.get_parent_guidance_notes(child_id=str(child_id), parent_id=parent_id, limit=limit)
        return {"child_id": str(child_id), "notes": notes}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching guidance notes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch guidance notes.")
