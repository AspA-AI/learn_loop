import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
from models.schemas import ChildProfile, ChildCreate, ChildUpdate, ParentInsight, ChildTopic, TopicCreate
from services.supabase_service import supabase_service
from agents.insight import insight_agent
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parent", tags=["parent"])

# Mock parent ID until Auth is fully integrated
MOCK_PARENT_ID = "00000000-0000-0000-0000-000000000000"

@router.get("/children", response_model=List[ChildProfile])
async def get_children():
    try:
        if not supabase_service.client:
            return []
        response = supabase_service.client.table("children").select("*").eq("parent_id", MOCK_PARENT_ID).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching children: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch children.")

@router.post("/children", response_model=ChildProfile)
async def create_child(request: ChildCreate):
    try:
        child = supabase_service.create_child(
            MOCK_PARENT_ID, 
            request.name, 
            request.age_level,
            learning_style=request.learning_style,
            interests=request.interests,
            reading_level=request.reading_level,
            attention_span=request.attention_span,
            strengths=request.strengths
        )
        return child
    except Exception as e:
        logger.error(f"Error creating child: {e}")
        raise HTTPException(status_code=500, detail="Failed to create child profile.")

@router.patch("/children/{child_id}", response_model=ChildProfile)
async def update_child(child_id: UUID, request: ChildUpdate):
    try:
        update_data = request.model_dump(exclude_unset=True)
        response = supabase_service.client.table("children").update(update_data).eq("id", str(child_id)).execute()
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
    child_ids: str = Form(...) # JSON string of UUIDs
):
    try:
        ids = json.loads(child_ids)
        
        # 1. Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # 2. Upload file to Supabase Storage
        file_path = f"curriculum/{MOCK_PARENT_ID}/{file.filename}"
        storage_response = supabase_service.upload_file_to_storage(
            bucket_name="curriculum",
            file_path=file_path,
            file_content=file_content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # 3. Store document metadata in database
        doc = supabase_service.add_curriculum_document(
            MOCK_PARENT_ID, 
            file.filename, 
            ids,
            storage_path=file_path,
            file_size=file_size
        )
        
        # 4. Vectorize and store in Weaviate (Placeholder for actual processing)
        # TODO: Implement PDF text extraction and Weaviate insertion
        
        return {"status": "success", "document": doc, "storage_path": file_path}
    except Exception as e:
        logger.error(f"Error uploading curriculum: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload curriculum.")

@router.get("/curriculum")
async def get_curriculum():
    try:
        response = supabase_service.client.table("curriculum_documents").select("*, children:child_curriculum(child_id)").eq("parent_id", MOCK_PARENT_ID).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching curriculum: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch curriculum.")

@router.get("/children/{child_id}/topics", response_model=List[ChildTopic])
async def get_child_topics(child_id: UUID):
    """Get all topics for a specific child"""
    try:
        topics = supabase_service.get_child_topics(str(child_id))
        return topics
    except Exception as e:
        logger.error(f"Error fetching child topics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch child topics.")

@router.post("/children/{child_id}/topics", response_model=ChildTopic)
async def add_child_topic(child_id: UUID, request: TopicCreate):
    """Add a new topic to a child"""
    try:
        topic = supabase_service.add_child_topic(
            str(child_id),
            request.topic,
            set_as_active=request.set_as_active
        )
        return topic
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding child topic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add topic.")

@router.patch("/children/{child_id}/topics/{topic_id}/activate", response_model=ChildTopic)
async def activate_topic(child_id: UUID, topic_id: UUID):
    """Set a topic as active (deactivates all other topics for this child)"""
    try:
        topic = supabase_service.set_active_topic(str(child_id), str(topic_id))
        return topic
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating topic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to activate topic.")

@router.delete("/children/{child_id}/topics/{topic_id}")
async def remove_child_topic(child_id: UUID, topic_id: UUID):
    """Remove a topic from a child. Only allowed if topic has no sessions."""
    try:
        success = supabase_service.remove_child_topic(str(child_id), str(topic_id))
        return {"success": success, "message": "Topic removed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing child topic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove topic.")

@router.get("/children/{child_id}/evaluations")
async def get_child_evaluations(child_id: UUID):
    """Get all evaluation reports for a specific child"""
    try:
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
async def get_child_sessions(child_id: UUID):
    """Get all sessions (completed and active) for a specific child"""
    try:
        if not supabase_service.client:
            return {"child_id": str(child_id), "sessions": []}
        
        sessions_response = supabase_service.client.table("sessions").select("*").eq("child_id", str(child_id)).order("created_at", desc=True).execute()
        
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

@router.get("/insights", response_model=Dict[str, Any])
async def get_insights(week: Optional[str] = Query(None)):
    """Get aggregated insights and mastery stats for parent's children from stored reports"""
    try:
        # 1. Get all completed sessions with evaluation reports
        sessions = supabase_service.get_sessions_for_parent(MOCK_PARENT_ID)
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
