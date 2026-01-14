import pytest
from agents.explainer import explainer_agent
from models.schemas import AgeLevel

@pytest.mark.asyncio
async def test_get_initial_explanation(mock_openai_service):
    # Setup
    mock_openai_service.return_value = "This is a test explanation."
    
    # Execute
    result = await explainer_agent.get_initial_explanation("Gravity", AgeLevel.SIX)
    
    # Assert
    assert result == "This is a test explanation."
    mock_openai_service.assert_called_once()
    # Verify system prompt contains age level info
    args, kwargs = mock_openai_service.call_args
    messages = args[0]
    assert "Age 6" in messages[0]["content"]

@pytest.mark.asyncio
async def test_get_initial_explanation_with_interests(mock_openai_service):
    # Setup
    mock_openai_service.return_value = "Plants are like green factories."
    context = {"interests": ["factories"]}
    
    # Execute
    result = await explainer_agent.get_initial_explanation("Photosynthesis", AgeLevel.EIGHT, context)
    
    # Assert
    assert result == "Plants are like green factories."
    args, kwargs = mock_openai_service.call_args
    messages = args[0]
    assert "factories" in messages[1]["content"]

