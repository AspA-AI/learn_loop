import logging
import json
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query, Body
from models.schemas import SessionStartRequest, SessionStartResponse, InteractionResponse, UnderstandingState, SessionEndRequest, SessionEndResponse
from pydantic import BaseModel, Field
from fastapi.responses import Response
from agents.explainer import explainer_agent
from agents.evaluator import evaluator_agent
from agents.insight import insight_agent
from services.supabase_service import supabase_service
from services.weaviate_service import weaviate_service
from services.openai_service import openai_service
from services.opik_service import opik_service, set_opik_thread_id
from utils.curriculum_reader import read_curriculum_files
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])

# In-memory quiz state storage (keyed by session_id)
# Format: {session_id: {"questions": [...], "current_index": 0, "answers": [...], "scores": [...]}}
quiz_states: Dict[str, Dict[str, Any]] = {}

# In-memory session context storage (keyed by session_id)
# Stores retrieved document chunks for the entire session to avoid repeated RAG calls
# Format: {session_id: "combined_context_string"}
session_contexts: Dict[str, str] = {}


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: str = Field(default="alloy", min_length=1, max_length=32)

@router.post("/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    try:
        # 1. Lookup child by Learning Code
        child = supabase_service.get_child_by_code(request.learning_code)
        if not child:
            raise HTTPException(status_code=404, detail="Invalid Learning Code. Please check with your parent!")
        
        child_id = child["id"]
        age_level = child["age_level"]
        
        # Get active topic from child_topics table
        active_topic = supabase_service.get_active_topic(child_id)
        if not active_topic:
            # Fallback to target_topic for backward compatibility
            concept = child.get("target_topic")
            if not concept:
                raise HTTPException(status_code=400, detail="No active topic has been assigned for you yet. Ask your parent to set a topic!")
        else:
            concept = active_topic["topic"]

        # 2. Create session in Supabase
        session_id = supabase_service.create_session(child_id, concept, age_level)
        
        # 3. Retrieve ALL document chunks for this topic ONCE at session start
        # This avoids repeated RAG calls during the conversation
        subject = active_topic.get("subject") if active_topic else None
        document_context = weaviate_service.retrieve_all_topic_chunks(
            child_id=child_id,
            topic=concept,
            subject=subject
        )
        
        # 4. Get curriculum files for this child and read their content
        logger.info(f"📚 [SESSION START] Retrieving curriculum for child_id: {child_id}")
        curriculum_files = supabase_service.get_child_curriculum_files(child_id)
        logger.info(f"📚 [SESSION START] Found {len(curriculum_files) if curriculum_files else 0} curriculum files")
        curriculum_content = read_curriculum_files(curriculum_files) if curriculum_files else None
        
        # 5. Fetch newest parent guidance notes (append-only) to steer future sessions
        # Keep this bounded to manage tokens.
        guidance_notes_rows = supabase_service.get_parent_guidance_notes(child_id=child_id, limit=6)
        guidance_notes = [n.get("note") for n in guidance_notes_rows if n.get("note")]

        # 6. Combine all context sources
        context_parts = []
        
        if document_context:
            context_parts.append(f"Reference Documents for Topic '{concept}':\n{document_context}")
            logger.info(f"📚 [SESSION START] Retrieved document context for topic '{concept}' ({len(document_context)} chars)")
        
        if curriculum_content:
            context_parts.append(f"Child's Curriculum Materials:\n{curriculum_content}")
            logger.info(f"📖 [SESSION START] Loaded curriculum content ({len(curriculum_content)} chars)")

        if guidance_notes:
            notes_block = "\n".join([f"- {n}" for n in guidance_notes])
            context_parts.append(
                "Parent guidance notes (apply these preferences throughout the session; do not mention them explicitly to the child unless asked):\n"
                f"{notes_block}"
            )
            logger.info(f"📝 [SESSION START] Loaded {len(guidance_notes)} parent guidance notes")
        
        # Combine all context
        combined_context = "\n\n---\n\n".join(context_parts) if context_parts else None
        
        # Store combined context in memory for this session
        if combined_context:
            session_contexts[session_id] = combined_context
            logger.info(f"💾 [SESSION START] Cached combined context ({len(combined_context)} chars)")
        else:
            logger.info(f"📚 [SESSION START] No document chunks or curriculum found for topic '{concept}'")
        
        # 7. Fallback to general curriculum context (RAG) if no documents, curriculum, or guidance
        grounding_context = combined_context
        if not grounding_context:
            grounding_context = weaviate_service.retrieve_curriculum_context(concept, age_level)
        
        # 8. Extract learning profile from child data (if available)
        learning_profile = None
        if any(child.get(key) for key in ["learning_style", "interests", "reading_level", "attention_span", "strengths"]):
            learning_profile = {
                "learning_style": child.get("learning_style"),
                "interests": child.get("interests"),
                "reading_level": child.get("reading_level"),
                "attention_span": child.get("attention_span"),
                "strengths": child.get("strengths")
            }
        
        learning_language = child.get("learning_language", "English")
        logger.info(f"🌍 [SESSION START] Child's learning language: {learning_language}")
        
        # 9. Translate concept name if needed for the child's UI
        localized_concept = await explainer_agent.translate_concept(concept, learning_language)
        
        # 10. Get initial explanation from Explainer Agent
        initial_explanation = await explainer_agent.get_initial_explanation(
            concept=concept,
            age_level=age_level,
            child_name=child["name"],
            grounding_context=grounding_context,
            learning_profile=learning_profile,
            language=learning_language
        )
        
        # 11. Save initial interaction to Supabase
        supabase_service.add_interaction(session_id, "assistant", initial_explanation)
        
        # All academic concepts follow the structured flow: greeting → story → academic → ongoing
        return SessionStartResponse(
            session_id=UUID(session_id),
            child_name=child["name"],
            child_id=UUID(child_id),
            learning_code=child.get("learning_code", ""),
            concept=concept,
            localized_concept=localized_concept,
            age_level=age_level,
            initial_explanation=initial_explanation,
            suggested_questions=["What happens next?", "Tell me more!"],
            conversation_phase="greeting",  # All concepts start with greeting phase
            learning_language=learning_language
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
    # Group child multi-turn interactions in Opik under one thread
    set_opik_thread_id(f"child_session:{session_id}")
    try:
        with opik_service.trace(
            name="session.interact",
            input={"session_id": session_id, "has_audio": bool(audio), "has_text": bool(message)},
            metadata={"route": "/sessions/{session_id}/interact"},
            tags=["child", "session"],
        ):
            # 1. Get session and child info FIRST to determine language
            try:
                session = supabase_service.get_session(session_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

            child_id = session.get("child_id")
            learning_language = "English"
            if child_id and supabase_service.client:
                try:
                    child_response = supabase_service.client.table("children").select("learning_language").eq("id", child_id).execute()
                    if child_response.data:
                        learning_language = child_response.data[0].get("learning_language", "English")
                        logger.info(f"🌍 [INTERACT] Using learning language: {learning_language}")
                except Exception as e:
                    logger.warning(f"Could not fetch learning language: {e}")

        # 2. Handle Input (Text or Audio)
        child_message = message
        transcribed_text = None

        if audio:
            logger.info(f"Processing audio input for session {session_id} in {learning_language}")
            try:
                audio_content = await audio.read()
                file_tuple = (audio.filename, audio_content, audio.content_type)
                # Pass the learning language to Whisper for better accuracy
                transcribed_text = await openai_service.transcribe_audio(file_tuple, language=learning_language)
                child_message = transcribed_text
                logger.info(f"Transcription result: {child_message}")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise HTTPException(status_code=400, detail="Failed to process audio input.")
        
        if not child_message:
            raise HTTPException(status_code=400, detail="Either 'message' or 'audio' must be provided.")

        # 3. Get history from Supabase
        history_data = supabase_service.get_interactions(session_id)
        
        # Get full child data for learning profile
        learning_profile = None
        if child_id and supabase_service.client:
            try:
                child_response = supabase_service.client.table("children").select("*").eq("id", child_id).execute()
                if child_response.data:
                    child = child_response.data[0]
                    # learning_language already set above
                    if any(child.get(key) for key in ["learning_style", "interests", "reading_level", "attention_span", "strengths"]):
                        learning_profile = {
                            "learning_style": child.get("learning_style"),
                            "interests": child.get("interests"),
                            "reading_level": child.get("reading_level"),
                            "attention_span": child.get("attention_span"),
                            "strengths": child.get("strengths")
                        }
            except Exception as e:
                logger.warning(f"Could not fetch learning profile: {e}")
        
        # Format history for OpenAI
        history = [{"role": item["role"], "content": item["content"]} for item in history_data]
        last_explanation = history[-1]["content"] if history else ""
        
        # Determine conversation phase for step-by-step flow (for ALL academic concepts)
        # All concepts follow the same structure: greeting → story → story quiz → academic → academic quiz → ongoing
        conversation_phase = "ongoing"
        # Check conversation history to determine phase
        assistant_messages = [h["content"] for h in history_data if h.get("role") == "assistant"]
        user_messages = [h["content"] for h in history_data if h.get("role") == "user"]
        
        if len(assistant_messages) == 1:  # Only greeting
            # Check if child is ready
            ready_keywords = ["ready", "yes", "ok", "okay", "sure", "let's go", "start"]
            if any(keyword in child_message.lower() for keyword in ready_keywords):
                conversation_phase = "story_explanation"
            else:
                conversation_phase = "greeting"
        elif len(assistant_messages) == 2:  # Greeting + story explanation
            conversation_phase = "story_quiz"
        elif len(assistant_messages) == 3:  # Greeting + story + academic explanation
            conversation_phase = "academic_quiz"
        else:
            conversation_phase = "ongoing"
        
        # NOTE: Real-time evaluation has been removed. Evaluation now happens only at session end.
        # The explainer agent will adapt based on conversation flow without explicit understanding_state.
        
        # Initialize quiz option and visual exercise
        can_take_quiz = False
        visual_exercise = None  # Will be set if learning style is visual
        
        # 4. Get adaptive response from Explainer Agent (step-by-step for math)
        # Use stored document context from session start (avoids repeated RAG calls)
        grounding_context = session_contexts.get(session_id)
        if not grounding_context:
            # Fallback to general curriculum context if no subject documents
            grounding_context = weaviate_service.retrieve_curriculum_context(session["concept"], session["age_level"])
        
        # Handle step-by-step flow for ALL academic concepts
        if conversation_phase == "story_explanation":
            # Step 1: Child said ready, give story explanation with quiz
            # COMMENTED OUT: Visual exercise feature (keeping for future implementation)
            # is_visual_learner = learning_profile and learning_profile.get("learning_style", "").lower() == "visual"
            # 
            # if is_visual_learner:
            #     # For visual learners: VERY short story, then immediate visual exercise
            #     logger.info("🎨 [VISUAL] Short story + visual exercise for visual learner")
            #     agent_response = await explainer_agent.get_story_explanation(
            #         concept=session["concept"],
            #         age_level=session["age_level"],
            #         child_name="there",
            #         grounding_context=grounding_context,
            #         learning_profile=learning_profile,
            #         language=learning_language
            #     )
            #     # Keep story VERY short - truncate to first sentence only
            #     sentences = agent_response.split('.')
            #     if len(sentences) > 0:
            #         agent_response = sentences[0].strip() + '.'
            #     else:
            #         agent_response = agent_response[:100] + '...'  # Fallback truncation
            #     
            #     # Generate visual exercise immediately for visual learners
            #     visual_exercise = await explainer_agent.generate_visual_exercise(
            #         concept=session["concept"],
            #         age_level=session["age_level"],
            #         child_name="there",
            #         learning_profile=learning_profile,
            #         language=learning_language
            #     )
            #     if visual_exercise:
            #         logger.info(f"🎨 [VISUAL] Generated exercise type: {visual_exercise.get('exercise_type')}")
            #     else:
            #         logger.warning("🎨 [VISUAL] Failed to generate visual exercise")
            # else:
            #     # For non-visual learners: normal story explanation
            agent_response = await explainer_agent.get_story_explanation(
                concept=session["concept"],
                age_level=session["age_level"],
                child_name="there",
                grounding_context=grounding_context,
                learning_profile=learning_profile,
                language=learning_language
            )
            
            can_end_session = False
            should_offer_end = False
            conversation_phase = "story_quiz"
            # State is already set to PROCEDURAL by the gatekeeper above
        elif conversation_phase == "story_quiz":
            # Step 2: Child answered story quiz, evaluate and then give academic explanation
            # Evaluate their answer first (already done above)
            # Then give academic explanation
            agent_response = await explainer_agent.get_academic_explanation(
                concept=session["concept"],
                age_level=session["age_level"],
                child_name="there",
                story_explanation=last_explanation,
                grounding_context=grounding_context,
                learning_profile=learning_profile,
                language=learning_language
            )
            # Also give academic quiz right after
            academic_quiz = await explainer_agent.get_academic_quiz(
                concept=session["concept"],
                age_level=session["age_level"],
                child_name="there",
                grounding_context=grounding_context,
                learning_profile=learning_profile,
                language=learning_language
            )
            agent_response += "\n\n" + academic_quiz
            # COMMENTED OUT: Visual exercise feature (keeping for future implementation)
            # # Check if visual learning style - generate visual exercise instead of text quiz
            # visual_exercise = None
            # is_visual_learner = learning_profile and learning_profile.get("learning_style", "").lower() == "visual"
            # 
            # if is_visual_learner:
            #     # Generate visual exercise for visual learners
            #     logger.info("🎨 [VISUAL] Generating visual exercise for visual learner")
            #     visual_exercise = await explainer_agent.generate_visual_exercise(
            #         concept=session["concept"],
            #         age_level=session["age_level"],
            #         child_name="there",
            #         learning_profile=learning_profile,
            #         language=learning_language
            #     )
            #     if visual_exercise:
            #         agent_response += f"\n\n{visual_exercise.get('instruction', 'Complete the exercise below!')}"
            # else:
            #     # Text-based quiz for non-visual learners
            #     academic_quiz = await explainer_agent.get_academic_quiz(
            #         concept=session["concept"],
            #         age_level=session["age_level"],
            #         child_name="there",
            #         learning_profile=learning_profile,
            #         language=learning_language
            #     )
            #     agent_response += "\n\n" + academic_quiz
            
            can_end_session = False
            should_offer_end = False
            conversation_phase = "academic_quiz"
        else:
            # Normal adaptive response for ongoing conversation (including academic_quiz phase and beyond)
            # NOTE: No understanding_state passed - evaluation happens only at session end
            agent_response, can_end_session, should_offer_end = await explainer_agent.get_adaptive_response(
                concept=session["concept"],
                age_level=session["age_level"],
                child_message=child_message,
                history=history,
                grounding_context=grounding_context,
                understanding_state=None,  # No real-time evaluation
                confusion_attempts=0,  # No confusion tracking during conversation
                learning_profile=learning_profile,
                language=learning_language
            )
        
        # NOTE: We no longer auto-enable can_end_session or calculate mastery during conversation.
        # Ending the session is now an explicit action from the frontend (parent/child clicks end).
        # Full evaluation with mastery calculation happens only when end_session is called.
        logger.info(f"🏁 [DECISION] Final flags -> can_end_session: {can_end_session}, can_take_quiz: {can_take_quiz}")
        
        # COMMENTED OUT: Visual exercise feature for ongoing phase (keeping for future implementation)
        # # Check if we should generate visual exercise for visual learners in ongoing phase
        # if visual_exercise is None and conversation_phase == "ongoing":
        #     is_visual_learner = learning_profile and learning_profile.get("learning_style", "").lower() == "visual"
        #     if is_visual_learner and state == UnderstandingState.UNDERSTOOD:
        #         # Offer visual exercise when they understand a concept
        #         logger.info("🎨 [VISUAL] Generating visual exercise for ongoing conversation")
        #         visual_exercise = await explainer_agent.generate_visual_exercise(
        #             concept=session["concept"],
        #             age_level=session["age_level"],
        #             child_name="there",
        #             learning_profile=learning_profile,
        #             language=learning_language
        #         )
        #         if visual_exercise:
        #             agent_response += f"\n\n{visual_exercise.get('instruction', 'Try this visual exercise!')}"
        
        # 5. Save interactions to Supabase (no understanding_state stored during conversation)
        supabase_service.add_interaction(session_id, "user", child_message)
        supabase_service.add_interaction(session_id, "assistant", agent_response, None)  # No real-time evaluation
        
        # Check if quiz is active
        quiz_active = session_id in quiz_states
        quiz_question = None
        quiz_question_number = None
        quiz_total_questions = None
        
        if quiz_active:
            quiz_state = quiz_states[session_id]
            current_index = quiz_state.get("current_index", 0)
            questions = quiz_state.get("questions", [])
            if current_index < len(questions):
                quiz_question = questions[current_index]
                quiz_question_number = current_index + 1
                quiz_total_questions = len(questions)
        
        return InteractionResponse(
            agent_response=agent_response,
            transcribed_text=transcribed_text,
            understanding_state=UnderstandingState.PROCEDURAL,  # No real-time evaluation - default to procedural
            follow_up_hint=None,  # No real-time evaluation - no hints during conversation
            can_end_session=can_end_session,
            can_take_quiz=can_take_quiz,
            conversation_phase=conversation_phase,
            quiz_active=quiz_active,
            quiz_question=quiz_question,
            quiz_question_number=quiz_question_number,
            quiz_total_questions=quiz_total_questions,
            visual_exercise=None  # COMMENTED OUT: visual_exercise feature (keeping for future implementation)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during interaction for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during the interaction.")


@router.post("/{session_id}/tts")
async def tts(session_id: str, request: TTSRequest):
    """
    Generate speech audio for a given text in the context of a child session.
    Returns MP3 bytes. Used by child UI to "play" assistant messages.
    """
    try:
        # Verify session exists and fetch child's learning language for pronunciation
        session = supabase_service.get_session(session_id)
        child_id = session.get("child_id")
        learning_language = "English"
        if child_id and supabase_service.client:
            try:
                child_response = supabase_service.client.table("children").select("learning_language").eq("id", child_id).execute()
                if child_response.data:
                    learning_language = child_response.data[0].get("learning_language", "English")
            except Exception as e:
                logger.warning(f"Could not fetch learning language for TTS: {e}")

        set_opik_thread_id(f"child_session:{session_id}")
        with opik_service.trace(
            name="session.tts",
            input={"session_id": session_id, "text_len": len(request.text or ""), "voice": request.voice},
            metadata={"route": "/sessions/{session_id}/tts"},
            tags=["child", "tts"],
        ):
            audio_bytes = await openai_service.text_to_speech(
                text=request.text,
                language=learning_language,
                voice=request.voice,
            )

        return Response(content=audio_bytes, media_type="audio/mpeg")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during TTS for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate speech.")

@router.post("/{session_id}/end", response_model=SessionEndResponse)
async def end_session(session_id: str, request: Optional[SessionEndRequest] = Body(None)):
    """End a session and generate evaluation report. Optionally accepts duration_seconds in request body."""
    try:
        # 1. Get session and all interactions
        try:
            session = supabase_service.get_session(session_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Session not found. Please start a new session.")
        
        # Get child info for name and language
        child = supabase_service.get_child_by_id(session["child_id"])
        child_name = child.get("name", "Child") if child else "Child"
        learning_language = child.get("learning_language", "English") if child else "English"
        
        if session.get("status") == "completed":
            # Return existing report if already ended
            return SessionEndResponse(
                success=True,
                evaluation_report=session.get("evaluation_report", {})
            )
        
        interactions = supabase_service.get_interactions(session_id)
        
        # 2. Generate academic snapshot and metrics using EvaluatorAgent
        academic_report = await evaluator_agent.generate_session_report(
            child_name=child_name,
            concept=session["concept"],
            interactions=interactions,
            language=learning_language
        )
        
        # 3. Prepare session data for InsightAgent (legacy report format)
        sessions_data = [{
            "session_id": session_id,
            "concept": session["concept"],
            "child_name": child_name,
            "created_at": session.get("created_at"),
            "interactions": [
                {
                    "role": i["role"],
                    "content": i["content"],
                    "understanding_state": i.get("understanding_state")
                }
                for i in interactions
            ]
        }]
        
        # 4. Generate evaluation report using InsightAgent
        report = await insight_agent.generate_parent_report(sessions_data)

        # 4b. Update child's aggregated curriculum coverage (token-efficient for advisor agent)
        try:
            child_id_str = str(session["child_id"])
            # Rebuild the same grounding context style used at session start
            curriculum_files = supabase_service.get_child_curriculum_files(child_id_str)
            curriculum_content = read_curriculum_files(curriculum_files) if curriculum_files else None
            document_context = weaviate_service.retrieve_all_topic_chunks(child_id=child_id_str, topic=session["concept"])

            context_parts = []
            if document_context:
                context_parts.append(f"Reference Documents for Topic '{session['concept']}':\n{document_context}")
            if curriculum_content:
                context_parts.append(f"Child's Curriculum Materials:\n{curriculum_content}")
            grounding_context = "\n\n---\n\n".join(context_parts) if context_parts else None

            covered_items: List[str] = []
            if grounding_context:
                covered_items = await insight_agent.extract_session_curriculum_coverage(
                    concept=session["concept"],
                    interactions=interactions,
                    grounding_context=grounding_context,
                )

            if child and isinstance(child, dict):
                existing = child.get("curriculum_coverage") or {}
            else:
                existing = {}

            if not isinstance(existing, dict):
                existing = {}

            # Stored structure:
            # {
            #   "covered_items": ["..."],
            #   "last_updated": "ISO",
            #   "by_concept": { "Addition": ["..."] }
            # }
            all_items = existing.get("covered_items") if isinstance(existing.get("covered_items"), list) else []
            by_concept = existing.get("by_concept") if isinstance(existing.get("by_concept"), dict) else {}

            # Merge + dedupe (preserve order)
            merged_all: List[str] = []
            for it in (all_items + (covered_items or [])):
                s = str(it or "").strip()
                if s and s not in merged_all:
                    merged_all.append(s)

            if covered_items:
                concept_key = str(session["concept"])
                prev_concept_items = by_concept.get(concept_key)
                if not isinstance(prev_concept_items, list):
                    prev_concept_items = []
                merged_concept: List[str] = []
                for it in (prev_concept_items + covered_items):
                    s = str(it or "").strip()
                    if s and s not in merged_concept:
                        merged_concept.append(s)
                by_concept[concept_key] = merged_concept

            new_snapshot = {
                "covered_items": merged_all,
                "by_concept": by_concept,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            supabase_service.update_child_curriculum_coverage(child_id_str, new_snapshot)
        except Exception as e:
            logger.warning(f"Failed to update child curriculum coverage snapshot: {e}")
        
        # 5. End-of-session grading: compute mastery from per-question answer scores (not by LLM)
        # 5a. Ask EvaluatorAgent to grade individual question/answer pairs
        answer_evaluation = await evaluator_agent.evaluate_answers(
            concept=session["concept"],
            interactions=interactions,
            language=learning_language,
        )
        questions_info = answer_evaluation.get("questions") or []

        # 5b. Aggregate correctness and relevance into a numeric mastery score
        corr_scores: List[float] = []
        rel_scores: List[float] = []
        for q in questions_info:
            try:
                c = float(q.get("answer_correctness", 0) or 0)
                corr_scores.append(max(0.0, min(100.0, c)))
            except Exception:
                continue
        for q in questions_info:
            try:
                r = float(q.get("answer_relevance", 0) or 0)
                rel_scores.append(max(0.0, min(100.0, r)))
            except Exception:
                continue

        avg_corr = sum(corr_scores) / len(corr_scores) if corr_scores else None
        avg_rel = sum(rel_scores) / len(rel_scores) if rel_scores else None

        # Check for quiz performance (if any) so we can combine it with answer-based mastery
        quiz_percentage = None
        if session_id in quiz_states:
            quiz_state = quiz_states[session_id]
            quiz_scores = quiz_state.get("scores", [])
            if quiz_scores:
                total_quiz_score = sum(quiz_scores)
                max_quiz_score = len(quiz_scores) * 100
                quiz_percentage = (total_quiz_score / max_quiz_score * 100) if max_quiz_score > 0 else 0
        
        # 5c. Compute mastery_percent using a deterministic algorithm (not by LLM)
        if avg_corr is not None:
            # Start from answer correctness average
            base_mastery_from_answers = avg_corr

            # If the child is basically not addressing the questions (very low relevance),
            # clamp to a conservative band (around 35%) instead of extreme 0%.
            if avg_rel is not None and avg_rel < 30:
                base_mastery_from_answers = 35.0

            if quiz_percentage is not None:
                mastery_percent = int(
                    base_mastery_from_answers * 0.4 + quiz_percentage * 0.6
                )
            else:
                mastery_percent = int(base_mastery_from_answers)
        else:
            # Fallback: no clear Q/A pairs detected; fall back to previous understanding-state heuristic.
            states = [
                i.get("understanding_state")
                for i in interactions
                if i.get("understanding_state")
                and i.get("understanding_state") != "procedural"
            ]
            total = len(states)
            understood = states.count("understood") if total > 0 else 0
            partial = states.count("partial") if total > 0 else 0
            confused = states.count("confused") if total > 0 else 0

            base_mastery = 0.0
            if total > 0:
                base_mastery = (
                    (understood * 1.0 + partial * 0.6 + confused * 0.2) / total
                ) * 100

            if quiz_percentage is not None:
                mastery_percent = int(
                    base_mastery * 0.4 + quiz_percentage * 0.6
                )
            else:
                mastery_percent = int(base_mastery)
        
        # Ensure mastery is between 0 and 100
        mastery_percent = max(0, min(100, mastery_percent))
        
        # 6. Enrich report with session metadata
        evaluation_report = {
            **report,
            "session_id": session_id,
            "concept": session["concept"],
            "mastery_percent": mastery_percent,
            "total_interactions": len(interactions),
            # understanding-state counts are still useful to inspect, but no longer drive mastery_percent directly
            "answer_evaluation": answer_evaluation,
            "metrics": academic_report.get("metrics", {}),
            "academic_summary": academic_report.get("summary", ""),
            "ended_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 7. Save report, metrics and summary to database
        # Use duration from request body if provided, otherwise calculate from timestamps
        duration_seconds = request.duration_seconds if request and hasattr(request, 'duration_seconds') else None
        supabase_service.end_session(
            session_id=session_id, 
            evaluation_report=evaluation_report,
            metrics=academic_report.get("metrics"),
            academic_summary=academic_report.get("summary"),
            duration_seconds=duration_seconds
        )

        # Clean up any active quiz state for this session (if the child ended during a quiz)
        if session_id in quiz_states:
            del quiz_states[session_id]
            logger.info(f"🧹 [SESSION END] Cleared quiz state for session {session_id}")
        
        # 7. Clean up session context from memory
        if session_id in session_contexts:
            del session_contexts[session_id]
            logger.info(f"🧹 [SESSION END] Cleaned up cached context for session {session_id}")
        
        return SessionEndResponse(
            success=True,
            evaluation_report=evaluation_report
        )
    except HTTPException:
        raise
    except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to end session and generate report.")

@router.post("/{session_id}/quiz/start")
async def start_quiz(session_id: str, num_questions: int = Query(5, ge=3, le=10)):
    """Start a practice quiz for the session"""
    try:
        # 1. Get session and child info
        session = supabase_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        
        child = supabase_service.get_child_by_id(session["child_id"])
        if not child:
            raise HTTPException(status_code=404, detail="Child not found.")
        
        learning_profile = {
            "learning_style": child.get("learning_style"),
            "interests": child.get("interests"),
            "reading_level": child.get("reading_level"),
            "attention_span": child.get("attention_span"),
            "strengths": child.get("strengths")
        }
        
        # 2. Generate quiz questions
        learning_language = child.get("learning_language", "English")
        grounding_context = session_contexts.get(session_id)
        if not grounding_context:
            grounding_context = weaviate_service.retrieve_curriculum_context(session["concept"], session["age_level"])
        questions = await explainer_agent.generate_quiz_questions(
            concept=session["concept"],
            age_level=session["age_level"],
            child_name=child.get("name", "there"),
            num_questions=min(num_questions, 10),  # Cap at 10 questions
            grounding_context=grounding_context,
            learning_profile=learning_profile,
            language=learning_language
        )
        
        if not questions:
            raise HTTPException(status_code=500, detail="Failed to generate quiz questions.")
        
        # 3. Initialize quiz state
        quiz_states[session_id] = {
            "questions": questions,
            "current_index": 0,
            "answers": [],
            "scores": [],
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 4. Save quiz start message and first question to chat (exam-style, no story wrapper)
        first_question_text = questions[0]
        quiz_start_message = f"Quiz started: {session['concept']}.\nQuestion 1 of {len(questions)}:\n{first_question_text}"
        supabase_service.add_interaction(
            session_id,
            "assistant",
            quiz_start_message
        )
        
        # 5. Return first question
        return {
            "success": True,
            "quiz_active": True,
            "question": questions[0],
            "question_number": 1,
            "total_questions": len(questions),
            "message": quiz_start_message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start quiz.")

@router.post("/{session_id}/quiz/answer")
async def submit_quiz_answer(session_id: str, answer: str = Form(...)):
    """Submit an answer to the current quiz question"""
    try:
        # 1. Check if quiz is active
        if session_id not in quiz_states:
            raise HTTPException(status_code=400, detail="No active quiz for this session.")
        
        quiz_state = quiz_states[session_id]
        current_index = quiz_state.get("current_index", 0)
        questions = quiz_state.get("questions", [])
        
        if current_index >= len(questions):
            raise HTTPException(status_code=400, detail="Quiz already completed.")
        
        # 2. Get session and child info for evaluation
        session = supabase_service.get_session(session_id)
        child = supabase_service.get_child_by_id(session["child_id"])
        
        learning_profile = {
            "learning_style": child.get("learning_style"),
            "interests": child.get("interests"),
            "reading_level": child.get("reading_level"),
            "attention_span": child.get("attention_span"),
            "strengths": child.get("strengths")
        }
        
        # 3. Evaluate the answer
        current_question = questions[current_index]
        learning_language = child.get("learning_language", "English")
        evaluation = await explainer_agent.evaluate_quiz_answer(
            concept=session["concept"],
            age_level=session["age_level"],
            question=current_question,
            answer=answer,
            learning_profile=learning_profile,
            language=learning_language
        )
        
        # 4. Store answer and score
        quiz_state["answers"].append(answer)
        quiz_state["scores"].append(evaluation["score"])
        
        # 5. Move to next question or complete quiz
        quiz_state["current_index"] = current_index + 1
        next_index = current_index + 1
        
        if next_index >= len(questions):
            # Quiz completed - calculate results
            total_score = sum(quiz_state["scores"])
            max_score = len(questions) * 100
            percentage = int((total_score / max_score) * 100) if max_score > 0 else 0
            
            # Save quiz results to session
            supabase_service.add_interaction(
                session_id, 
                "user", 
                f"[Quiz Answer {current_index + 1}]: {answer}"
            )
            supabase_service.add_interaction(
                session_id,
                "assistant",
                f"[Quiz Feedback]: {evaluation['feedback']}\n\n🎉 Quiz Complete! You scored {percentage}%! Great job practicing {session['concept']}!"
            )
            
            # Clear quiz state
            del quiz_states[session_id]
            
            return {
                "success": True,
                "quiz_completed": True,
                "feedback": evaluation["feedback"],
                "correct": evaluation["correct"],
                "score": evaluation["score"],
                "total_score": total_score,
                "max_score": max_score,
                "percentage": percentage,
                "message": f"🎉 Quiz Complete! You scored {percentage}%! Would you like to take another quiz or end the session?",
                "can_take_another_quiz": True,
                "can_end_session": True
            }
        else:
            # More questions remaining
            # Save user answer to chat
            supabase_service.add_interaction(
                session_id,
                "user",
                f"Question {current_index + 1}: {answer}"
            )
            
            # Save feedback and next question to chat
            next_question_text = questions[next_index]
            feedback_message = f"{evaluation['feedback']}\n\n**Question {next_index + 1} of {len(questions)}:**\n{next_question_text}"
            supabase_service.add_interaction(
                session_id,
                "assistant",
                feedback_message
            )
            
            return {
                "success": True,
                "quiz_completed": False,
                "feedback": evaluation["feedback"],
                "correct": evaluation["correct"],
                "score": evaluation["score"],
                "next_question": questions[next_index],
                "question_number": next_index + 1,
                "total_questions": len(questions),
                "message": feedback_message  # Full message with feedback and next question
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz answer for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit quiz answer.")

@router.post("/{session_id}/quiz/cancel")
async def cancel_quiz(session_id: str):
    """Cancel the current quiz"""
    try:
        if session_id in quiz_states:
            del quiz_states[session_id]
        return {"success": True, "message": "Quiz cancelled."}
    except Exception as e:
        logger.error(f"Error cancelling quiz for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel quiz.")
