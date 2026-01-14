import pytest
import json
from agents.evaluator import evaluator_agent
from models.schemas import UnderstandingState

@pytest.mark.asyncio
async def test_evaluate_understanding_success(mock_openai_service):
    # Setup
    mock_response = {
        "state": "understood",
        "reasoning": "The child explained it well.",
        "follow_up_hint": "Move to the next topic."
    }
    mock_openai_service.return_value = json.dumps(mock_response)
    
    # Execute
    state, reasoning, hint = await evaluator_agent.evaluate_understanding(
        "Gravity", "Things fall down.", "I get it! Like an apple!"
    )
    
    # Assert
    assert state == UnderstandingState.UNDERSTOOD
    assert reasoning == "The child explained it well."
    assert hint == "Move to the next topic."

@pytest.mark.asyncio
async def test_evaluate_understanding_malformed_json(mock_openai_service):
    # Setup
    mock_openai_service.return_value = "Not a JSON"
    
    # Execute
    state, reasoning, hint = await evaluator_agent.evaluate_understanding(
        "Gravity", "Things fall down.", "I get it!"
    )
    
    # Assert
    assert state == UnderstandingState.CONFUSED
    assert "Error parsing" in reasoning

