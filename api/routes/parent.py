import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
from models.schemas import ChildProfile, ChildCreate, ChildUpdate, ParentInsight, ChildTopic, TopicCreate, ParentProfile
from services.supabase_service import supabase_service
from services.weaviate_service import weaviate_service
from agents.insight import insight_agent
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
