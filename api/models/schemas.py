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

# --- Child & Curriculum ---

class ChildProfile(BaseModel):
    id: UUID
    name: str
    age_level: AgeLevel
    learning_code: str
    target_topic: Optional[str] = None

class ChildCreate(BaseModel):
    name: str
    age_level: AgeLevel

class ChildUpdate(BaseModel):
    target_topic: Optional[str] = None
    age_level: Optional[AgeLevel] = None

# --- Session & Interaction ---

class SessionStartRequest(BaseModel):
    learning_code: str

class SessionStartResponse(BaseModel):
    session_id: UUID
    child_name: str
    concept: str
    age_level: AgeLevel
    initial_explanation: str
    suggested_questions: List[str]

class InteractionResponse(BaseModel):
    agent_response: str
    transcribed_text: Optional[str] = None
    understanding_state: UnderstandingState
    follow_up_hint: Optional[str] = None

# --- Parent Insights ---

class ParentInsight(BaseModel):
    summary: str
    achievements: List[str]
    challenges: List[str]
    recommended_next_steps: List[str]
