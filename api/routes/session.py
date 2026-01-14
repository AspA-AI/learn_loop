import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from models.schemas import SessionStartRequest, SessionStartResponse, InteractionResponse, UnderstandingState
from agents.explainer import explainer_agent
from agents.evaluator import evaluator_agent
from services.supabase_service import supabase_service
from services.weaviate_service import weaviate_service
from services.openai_service import openai_service
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    try:
        # 1. Lookup child by Learning Code
        child = supabase_service.get_child_by_code(request.learning_code)
        if not child:
            raise HTTPException(status_code=404, detail="Invalid Learning Code. Please check with your parent!")
        
        child_id = child["id"]
        age_level = child["age_level"]
        concept = child.get("target_topic")
        
        if not concept:
            raise HTTPException(status_code=400, detail="No topic has been assigned for you yet. Ask your parent to pin a topic!")

        # 2. Create session in Supabase
        session_id = supabase_service.create_session(child_id, concept, age_level)
        
        # 3. Check Weaviate for grounding context (RAG)
        # TODO: Filter by child's assigned curriculum in Weaviate
        grounding_context = weaviate_service.retrieve_curriculum_context(concept, age_level)
        
        # 4. Get initial explanation from Explainer Agent
        initial_explanation = await explainer_agent.get_initial_explanation(
            concept=concept,
            age_level=age_level,
            child_name=child["name"]
        )
        
        # 5. Save initial interaction to Supabase
        supabase_service.add_interaction(session_id, "assistant", initial_explanation)
        
        return SessionStartResponse(
            session_id=UUID(session_id),
            child_name=child["name"],
            concept=concept,
            age_level=age_level,
            initial_explanation=initial_explanation,
            suggested_questions=["What happens next?", "Tell me more!"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start learning session.")

@router.post("/{session_id}/interact", response_model=InteractionResponse)
async def interact(
    session_id: str, 
    message: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None)
):
    try:
        # 1. Handle Input (Text or Audio)
        child_message = message
        transcribed_text = None

        if audio:
            logger.info(f"Processing audio input for session {session_id}")
            try:
                audio_content = await audio.read()
                file_tuple = (audio.filename, audio_content, audio.content_type)
                transcribed_text = await openai_service.transcribe_audio(file_tuple)
                child_message = transcribed_text
                logger.info(f"Transcription result: {child_message}")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise HTTPException(status_code=400, detail="Failed to process audio input.")
        
        if not child_message:
            raise HTTPException(status_code=400, detail="Either 'message' or 'audio' must be provided.")

        # 2. Get session and history from Supabase
        try:
            session = supabase_service.get_session(session_id)
            history_data = supabase_service.get_interactions(session_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Format history for OpenAI
        history = [{"role": item["role"], "content": item["content"]} for item in history_data]
        last_explanation = history[-1]["content"] if history else ""
        
        # 3. Evaluate child's understanding
        state, reasoning, hint = await evaluator_agent.evaluate_understanding(
            concept=session["concept"],
            last_explanation=last_explanation,
            child_message=child_message
        )
        
        # 4. Get adaptive response from Explainer Agent
        agent_response = await explainer_agent.get_adaptive_response(
            concept=session["concept"],
            age_level=session["age_level"],
            child_message=child_message,
            history=history
        )
        
        # 5. Save interactions to Supabase
        supabase_service.add_interaction(session_id, "user", child_message)
        supabase_service.add_interaction(session_id, "assistant", agent_response, state)
        
        return InteractionResponse(
            agent_response=agent_response,
            transcribed_text=transcribed_text,
            understanding_state=state,
            follow_up_hint=hint
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during interaction for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during the interaction.")
