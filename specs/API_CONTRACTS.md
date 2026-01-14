# Learn Loop - API Contracts

## 1. Overview
The Learn Loop backend is a FastAPI application. All requests/responses are JSON-based unless otherwise specified.

## 2. Session Management (Child Side)

### 2.1 Start Learning Session
`POST /api/v1/sessions/start`

Starts a learning session using a child's unique Learning Code. The backend retrieves the parent's "Pinned Topic" and age level.

**Request Body**:
```json
{
  "learning_code": "LEO-782"
}
```

**Response**:
```json
{
  "session_id": "uuid-12345",
  "child_name": "Leo",
  "concept": "The Water Cycle",
  "age_level": 8,
  "initial_explanation": "Hey Leo! Imagine the Earth has a giant recycling machine for water...",
  "suggested_questions": ["Where does rain come from?", "How does water turn into clouds?"]
}
```

### 2.2 Submit Interaction
`POST /api/v1/sessions/{session_id}/interact`

**Request Body (Multipart/Form-Data)**:
- `message`: (Optional) Text message from the child.
- `audio`: (Optional) Audio file for Speech-to-Text processing.

**Response**:
```json
{
  "agent_response": "Exactly! It's like a never-ending cycle.",
  "transcribed_text": "So it just keeps going around?", 
  "understanding_state": "partial",
  "follow_up_hint": "Ask about evaporation next."
}
```

## 3. Parent Management (Admin Side)

### 3.1 Get Children Profiles
`GET /api/v1/parent/children`

**Response**:
```json
[
  {
    "id": "uuid",
    "name": "Leo",
    "age_level": 8,
    "learning_code": "LEO-782",
    "target_topic": "The Water Cycle"
  }
]
```

### 3.2 Update Child Profile
`PATCH /api/v1/parent/children/{child_id}`

**Request Body**:
```json
{
  "target_topic": "Photosynthesis",
  "age_level": 10
}
```

### 3.3 Upload Curriculum
`POST /api/v1/parent/curriculum/upload`

**Request Body (Multipart/Form-Data)**:
- `file`: The PDF/Text document.
- `child_ids`: List of UUIDs to assign this document to.

## 4. Schemas (Pydantic)

```python
class AgeLevel(int, Enum):
    SIX = 6
    EIGHT = 8
    TEN = 10

class UnderstandingState(str, Enum):
    UNDERSTOOD = "understood"
    PARTIAL = "partial"
    CONFUSED = "confused"

class SessionStartRequest(BaseModel):
    learning_code: str
```
