import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
from models.schemas import ChildProfile, ChildCreate, ChildUpdate, ParentInsight
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
        child = supabase_service.create_child(MOCK_PARENT_ID, request.name, request.age_level)
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
        # 1. Store in Supabase
        doc = supabase_service.add_curriculum_document(MOCK_PARENT_ID, file.filename, ids)
        
        # 2. Vectorize and store in Weaviate (Placeholder for actual processing)
        # TODO: Implement PDF text extraction and Weaviate insertion
        
        return {"status": "success", "document": doc}
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

@router.get("/insights", response_model=Dict[str, Any])
async def get_insights(week: Optional[str] = Query(None)):
    """Get aggregated insights and mastery stats for parent's children"""
    try:
        # 1. Get all sessions for parent's children
        sessions = supabase_service.get_sessions_for_parent(MOCK_PARENT_ID)
        
        if not sessions:
            return {
                "summary": "No learning sessions found yet.",
                "children_stats": [],
                "overall_mastery": 0,
                "total_sessions": 0,
                "total_hours": 0,
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Start a learning session to see progress!"]
            }
        
        # 2. Get all interactions with understanding states
        session_ids = [s["id"] for s in sessions]
        interactions = supabase_service.get_interactions_with_states(session_ids)
        
        # 3. Calculate mastery stats per child
        children_stats = []
        children_data = {}
        
        for session in sessions:
            child_id = session["child_id"]
            child_name = session.get("child_name", "Unknown")
            
            if child_id not in children_data:
                children_data[child_id] = {
                    "child_id": child_id,
                    "name": child_name,
                    "sessions": [],
                    "understanding_states": []
                }
            
            children_data[child_id]["sessions"].append(session)
        
        # Group interactions by session and calculate stats
        for interaction in interactions:
            session_id = interaction["session_id"]
            state = interaction.get("understanding_state")
            
            if state:
                # Find which child this session belongs to
                for session in sessions:
                    if session["id"] == session_id:
                        child_id = session["child_id"]
                        if child_id in children_data:
                            children_data[child_id]["understanding_states"].append(state)
                        break
        
        # Calculate mastery percentages
        for child_id, data in children_data.items():
            states = data["understanding_states"]
            total = len(states)
            
            if total == 0:
                mastery_percent = 0
                understood = 0
            else:
                understood = states.count("understood")
                partial = states.count("partial")
                # Weighted: understood=1.0, partial=0.5, confused=0.0
                mastery_percent = int(((understood * 1.0 + partial * 0.5) / total) * 100)
            
            # Calculate total hours (rough estimate: 5 min per interaction)
            total_interactions = len(states)
            estimated_hours = round((total_interactions * 5) / 60, 1)
            
            children_stats.append({
                "child_id": str(child_id),
                "name": data["name"],
                "mastery_count": understood,
                "mastery_percent": mastery_percent,
                "total_sessions": len(data["sessions"]),
                "total_hours": estimated_hours
            })
        
        # 4. Prepare data for InsightAgent
        sessions_data = []
        for session in sessions[:10]:  # Last 10 sessions
            session_interactions = [i for i in interactions if i["session_id"] == session["id"]]
            sessions_data.append({
                "session_id": session["id"],
                "concept": session["concept"],
                "child_name": session.get("child_name", "Unknown"),
                "created_at": session.get("created_at"),
                "interactions": [
                    {
                        "role": i["role"],
                        "content": i["content"][:200],  # Truncate for token efficiency
                        "understanding_state": i.get("understanding_state")
                    }
                    for i in session_interactions[:5]  # Last 5 interactions per session
                ]
            })
        
        # 5. Generate AI insights
        insight_report = await insight_agent.generate_parent_report(sessions_data)
        
        # 6. Calculate overall stats
        all_states = []
        for data in children_data.values():
            all_states.extend(data["understanding_states"])
        
        overall_mastery = 0
        if all_states:
            understood = all_states.count("understood")
            partial = all_states.count("partial")
            overall_mastery = int(((understood * 1.0 + partial * 0.5) / len(all_states)) * 100)
        
        total_hours = round((len(all_states) * 5) / 60, 1)
        
        return {
            "summary": insight_report.get("summary", "Learning progress summary"),
            "children_stats": children_stats,
            "overall_mastery": overall_mastery,
            "total_sessions": len(sessions),
            "total_hours": total_hours,
            "achievements": insight_report.get("achievements", []),
            "challenges": insight_report.get("challenges", []),
            "recommended_next_steps": insight_report.get("recommended_next_steps", [])
        }
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights.")
