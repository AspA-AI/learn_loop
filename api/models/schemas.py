from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID

class AgeLevel(int, Enum):
    SIX = 6
    EIGHT = 8
    TEN = 10

class UnderstandingState(str, Enum):
    UNDERSTOOD = "understood"
    PARTIAL = "partial"
    CONFUSED = "confused"
    PROCEDURAL = "procedural"  # For non-academic responses like "ready", "thanks", "ok"

# --- Child & Curriculum ---

class ChildProfile(BaseModel):
    id: UUID
    name: str
    age_level: int
    learning_code: str
    target_topic: Optional[str] = None
    # Optional Learning Profile
    learning_style: Optional[str] = None
    interests: Optional[List[str]] = None
    reading_level: Optional[str] = None
    attention_span: Optional[str] = None
    strengths: Optional[List[str]] = None
    learning_language: str = "English"

class ChildCreate(BaseModel):
    name: str
    age_level: int
    # Optional Learning Profile
    learning_style: Optional[str] = None
    interests: Optional[List[str]] = None
    reading_level: Optional[str] = None
    attention_span: Optional[str] = None
    strengths: Optional[List[str]] = None
    learning_language: str = "English"

class ChildUpdate(BaseModel):
    name: Optional[str] = None
    age_level: Optional[int] = None
    # Optional Learning Profile
    learning_style: Optional[str] = None
    interests: Optional[List[str]] = None
    reading_level: Optional[str] = None
    attention_span: Optional[str] = None
    strengths: Optional[List[str]] = None
    learning_language: Optional[str] = None

# --- Session & Interaction ---

class SessionStartRequest(BaseModel):
    learning_code: str

class SessionStartResponse(BaseModel):
    session_id: UUID
    child_name: str
    concept: str
    localized_concept: Optional[str] = None
    age_level: int  # Changed from AgeLevel enum to int for flexibility
    initial_explanation: str
    suggested_questions: List[str]
    conversation_phase: str = "greeting"  # "greeting" means waiting for ready
    learning_language: Optional[str] = None

class InteractionResponse(BaseModel):
    agent_response: str
    transcribed_text: Optional[str] = None
    understanding_state: UnderstandingState
    follow_up_hint: Optional[str] = None
    can_end_session: bool = False  # Indicates if child has understood and can end session
    conversation_phase: Optional[str] = None  # "greeting", "story_explanation", "story_quiz", "academic_explanation", "academic_quiz", "ongoing"
    can_take_quiz: bool = False  # Indicates if child can take a practice quiz
    quiz_active: bool = False  # Indicates if a quiz is currently active
    quiz_question: Optional[str] = None  # Current quiz question if quiz is active
    quiz_question_number: Optional[int] = None  # Current question number (e.g., 1 of 5)
    quiz_total_questions: Optional[int] = None  # Total questions in current quiz

class SessionEndRequest(BaseModel):
    session_id: UUID

class SessionEndResponse(BaseModel):
    success: bool
    evaluation_report: Dict[str, Any]

# --- Parent Insights ---
# Standardized Evaluation Report Format:
# {
#   "summary": str,  # 2-3 sentence summary
#   "achievements": List[str],  # 2-5 specific achievements
#   "challenges": List[str],  # 0-3 areas of difficulty
#   "recommended_next_steps": List[str],  # 2-4 actionable steps
#   "key_insights": List[str],  # 1-3 learning observations
#   "concept_mastery_level": str,  # "beginner" | "developing" | "proficient" | "mastered"
#   # Additional metadata added by end_session endpoint:
#   "session_id": str,
#   "concept": str,
#   "mastery_percent": int,
#   "total_interactions": int,
#   "understood_count": int,
#   "partial_count": int,
#   "confused_count": int,
#   "ended_at": str
# }

class ParentInsight(BaseModel):
    summary: str
    achievements: List[str]
    challenges: List[str]
    recommended_next_steps: List[str]
    key_insights: List[str] = []
    concept_mastery_level: str = "developing"  # beginner | developing | proficient | mastered

# --- Topic Management ---

class ChildTopic(BaseModel):
    id: UUID
    child_id: UUID
    subject: str
    topic: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None

class TopicCreate(BaseModel):
    subject: str
    topic: str
    set_as_active: bool = False  # If True, makes this topic active and deactivates others

class TopicUpdate(BaseModel):
    is_active: Optional[bool] = None

# --- Parent & Auth ---

class ParentProfile(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None
    preferred_language: str = "English"
