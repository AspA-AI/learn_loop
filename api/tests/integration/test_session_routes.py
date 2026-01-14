import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Learn Loop API", "status": "active"}

def test_start_session(mock_supabase_service, mock_weaviate_service, mock_openai_service):
    # Setup
    mock_openai_service.return_value = "Initial explanation text."
    
    # Execute
    response = client.post(
        "/api/v1/sessions/start",
        json={"age_level": 8, "concept": "Gravity"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id"
    assert data["initial_explanation"] == "Initial explanation text."
    mock_supabase_service.create_session.assert_called_once_with(8, "Gravity")

def test_interact_text(mock_supabase_service, mock_openai_service):
    # Setup
    mock_openai_service.side_effect = [
        '{"state": "partial", "reasoning": "Almost there", "follow_up_hint": "Explain more"}', # Evaluator
        "That is correct!" # Explainer
    ]
    
    # Execute
    response = client.post(
        "/api/v1/sessions/test-session-id/interact",
        data={"message": "Is it like a magnet?"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["agent_response"] == "That is correct!"
    assert data["understanding_state"] == "partial"
    mock_supabase_service.add_interaction.assert_called()

def test_interact_audio(mock_supabase_service, mock_openai_service, mocker):
    # Setup
    # Mock transcribe_audio
    mock_openai_service.side_effect = [
        "Transcribed text from audio", # STT
        '{"state": "understood", "reasoning": "Great job", "follow_up_hint": "Well done"}', # Evaluator
        "Excellent explanation!" # Explainer
    ]
    
    # Execute with a dummy audio file
    dummy_audio = (b"fake audio content", "test.wav", "audio/wav")
    response = client.post(
        "/api/v1/sessions/test-session-id/interact",
        files={"audio": ("test.wav", b"fake audio content", "audio/wav")}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["transcribed_text"] == "Transcribed text from audio"
    assert data["agent_response"] == "Excellent explanation!"
    assert data["understanding_state"] == "understood"

