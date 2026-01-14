import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_openai_service(mocker):
    # Patch the instance where it's used in agents, services, and routes
    mock = AsyncMock()
    mocker.patch("agents.explainer.openai_service.get_chat_completion", mock)
    mocker.patch("agents.evaluator.openai_service.get_chat_completion", mock)
    mocker.patch("agents.insight.openai_service.get_chat_completion", mock)
    mocker.patch("routes.session.openai_service.transcribe_audio", mock)
    mocker.patch("routes.session.openai_service.get_chat_completion", mock)
    return mock

@pytest.fixture
def mock_supabase_service(mocker):
    # Patch the instance where it's used in routes
    mock = MagicMock()
    mocker.patch("routes.session.supabase_service", mock)
    mocker.patch("routes.parent.supabase_service", mock)
    
    mock.create_session.return_value = "test-session-id"
    mock.get_session.return_value = {"id": "test-session-id", "age_level": 8, "concept": "Gravity"}
    mock.get_interactions.return_value = []
    mock.add_interaction = MagicMock()
    
    # Also patch the client if needed
    mock.client = MagicMock()
    return mock

@pytest.fixture
def mock_weaviate_service(mocker):
    mock = MagicMock()
    mocker.patch("routes.session.weaviate_service", mock)
    mock.retrieve_curriculum_context.return_value = None
    return mock
