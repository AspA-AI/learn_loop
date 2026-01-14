import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from models.schemas import ChildProfile, ChildCreate, ChildUpdate
from services.supabase_service import supabase_service
from typing import List, Optional
from uuid import UUID
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
