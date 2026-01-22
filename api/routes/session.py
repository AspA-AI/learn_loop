import logging
import json
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
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
        curriculum_files = supabase_service.get_child_curriculum_files(child_id)
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
        
        # 3. Evaluate child's understanding
        logger.info(f"🔍 [EVALUATION] Starting assessment for session: {session_id}")
        logger.info(f"📤 [EVALUATION] Concept: '{session['concept']}'")
        logger.info(f"📤 [EVALUATION] AI Last Message: \"{last_explanation}{'...' if len(last_explanation) > 100 else ''}\"")
        logger.info(f"📥 [EVALUATION] Child Response: \"{child_message}\"")

        state, reasoning, hint, performance_metrics = await evaluator_agent.evaluate_understanding(
            concept=session["concept"],
            last_explanation=last_explanation,
            child_message=child_message,
            language=learning_language
        )

        logger.info(f"✅ [EVALUATION] Result: {state.value.upper()}")
        logger.info(f"💡 [EVALUATION] Reasoning: {reasoning}")
        
        # Initialize quiz option
        can_take_quiz = False
        
        # Count consecutive confused states
        recent_states = [i.get("understanding_state") for i in history_data[-5:] if i.get("understanding_state")]
        confusion_attempts = 0
        if state == UnderstandingState.CONFUSED:
            # Count how many of the last few interactions were confused
            confusion_attempts = sum(1 for s in recent_states if s == "confused") + 1  # +1 for current
        elif state == UnderstandingState.UNDERSTOOD:
            # Reset confusion count if they understood
            confusion_attempts = 0
        elif state == UnderstandingState.PROCEDURAL:
            # If procedural, keep the previous confusion count (don't increment, don't reset)
            previous_states = [s for s in recent_states if s != "procedural"]
            if previous_states and previous_states[-1] == "confused":
                confusion_attempts = sum(1 for s in recent_states if s == "confused")
            else:
                confusion_attempts = 0
        
        # 4. Get adaptive response from Explainer Agent (step-by-step for math)
        # Use stored document context from session start (avoids repeated RAG calls)
        grounding_context = session_contexts.get(session_id)
        if not grounding_context:
            # Fallback to general curriculum context if no subject documents
            grounding_context = weaviate_service.retrieve_curriculum_context(session["concept"], session["age_level"])
        
        # Handle step-by-step flow for ALL academic concepts
        if conversation_phase == "story_explanation":
            # Step 1: Child said ready, give story explanation with quiz
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
                learning_profile=learning_profile,
                language=learning_language
            )
            agent_response += "\n\n" + academic_quiz
            can_end_session = False
            should_offer_end = False
            conversation_phase = "academic_quiz"
        else:
            # Normal adaptive response for ongoing conversation (including academic_quiz phase and beyond)
            agent_response, can_end_session, should_offer_end = await explainer_agent.get_adaptive_response(
                concept=session["concept"],
                age_level=session["age_level"],
                child_message=child_message,
                history=history,
                grounding_context=grounding_context,
                understanding_state=state.value,
                confusion_attempts=confusion_attempts,
                learning_profile=learning_profile,
                language=learning_language
            )
        
        # Only allow ending session if there's REAL evidence of understanding
        # Require at least 2 consecutive "understood" states with substantive responses
        if state == UnderstandingState.UNDERSTOOD:
            # Check if child provided substantive evidence (not just brief agreeable response)
            is_substantive = (
                len(child_message.split()) > 5 or  # More than just "OK" or "got it"
                any(word in child_message.lower() for word in ["because", "example", "like", "when", "if", "think"]) or
                "?" in child_message  # Asked a question
            )
            
            logger.info(f"📊 [DECISION] Substantive check: {is_substantive} (Message: \"{child_message}\")")
            
            if is_substantive:
                # Check last 2-3 interactions for consistent understanding (including current)
                recent_understood = [s for s in recent_states if s == "understood"]
                logger.info(f"📊 [DECISION] Recent understood states: {len(recent_understood)} in last 5 turns")
                
                # Current state is "understood", so we need at least 1 more in recent history
                if len(recent_understood) >= 1:  # Current + at least 1 previous = 2 total
                    can_end_session = True
                    can_take_quiz = True  # Offer quiz option when they've mastered it
                    logger.info("🎯 [DECISION] MASTERY REACHED: Enabling Quiz and End Session buttons")
                    # Add end session and quiz suggestion to the response
                    agent_response += "\n\n🎉 You've really mastered this! You can take a practice quiz to reinforce what you learned, or end this session and I'll create a summary of everything you learned today."
        
        # If child is stuck after multiple attempts, offer to end session
        if should_offer_end:
            logger.info("⚠️ [DECISION] Confusion threshold reached: Offering to end session")
            agent_response += "\n\n💙 Sometimes concepts take time to understand, and that's perfectly okay! If you'd like, we can end this session here. Your parent will see a summary of what we worked on today, and you can always come back to try again later."
            can_end_session = True  # Allow them to end even if confused

        logger.info(f"🏁 [DECISION] Final flags -> can_end_session: {can_end_session}, can_take_quiz: {can_take_quiz}")
        
        # 5. Save interactions to Supabase
        supabase_service.add_interaction(session_id, "user", child_message)
        supabase_service.add_interaction(session_id, "assistant", agent_response, state)
        
        # Store performance metrics if available (for mathematical concepts)
        if performance_metrics:
            # Store in a temporary way - we'll aggregate this in the evaluation report
            # For now, we can add it to the interaction metadata or aggregate at session end
            pass  # Will be aggregated in end_session
        
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
            understanding_state=state,
            follow_up_hint=hint,
            can_end_session=can_end_session,
            can_take_quiz=can_take_quiz,
            conversation_phase=conversation_phase,
            quiz_active=quiz_active,
            quiz_question=quiz_question,
            quiz_question_number=quiz_question_number,
            quiz_total_questions=quiz_total_questions
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
async def end_session(session_id: str):
    """End a session and generate evaluation report"""
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
        
        # 5. Calculate mastery stats
        states = [i.get("understanding_state") for i in interactions if i.get("understanding_state")]
        total = len(states)
        understood = states.count("understood") if total > 0 else 0
        partial = states.count("partial") if total > 0 else 0
        mastery_percent = int(((understood * 1.0 + partial * 0.5) / total) * 100) if total > 0 else 0
        
        # 6. Enrich report with session metadata
        evaluation_report = {
            **report,
            "session_id": session_id,
            "concept": session["concept"],
            "mastery_percent": mastery_percent,
            "total_interactions": len(interactions),
            "understood_count": understood,
            "partial_count": partial,
            "confused_count": states.count("confused") if total > 0 else 0,
            "metrics": academic_report.get("metrics", {}),
            "academic_summary": academic_report.get("summary", ""),
            "ended_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 7. Save report, metrics and summary to database
        supabase_service.end_session(
            session_id=session_id, 
            evaluation_report=evaluation_report,
            metrics=academic_report.get("metrics"),
            academic_summary=academic_report.get("summary")
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
        questions = await explainer_agent.generate_quiz_questions(
            concept=session["concept"],
            age_level=session["age_level"],
            child_name=child.get("name", "there"),
            num_questions=min(num_questions, 10),  # Cap at 10 questions
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
