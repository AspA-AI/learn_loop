import json
import logging
from services.openai_service import openai_service
from models.schemas import UnderstandingState
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self):
        self.system_prompt = (
            "You are an expert educational evaluator. Your job is to analyze a child's response "
            "to determine their level of understanding of a specific academic concept.\n\n"
            "You must classify the response into one of three states:\n"
            "1. 'understood': The child correctly applies the concept or explains it in their own words.\n"
            "2. 'partial': The child has the right idea but misses a key component or has a slight misconception.\n"
            "3. 'confused': The child expresses frustration, asks an unrelated question, or fundamentally misunderstands the analogy.\n\n"
            "Respond ONLY in JSON format with the following keys:\n"
            "- state: one of 'understood', 'partial', 'confused'\n"
            "- reasoning: a brief explanation of why you chose this state\n"
            "- follow_up_hint: a suggestion for the teacher on what to address next"
        )

    async def evaluate_understanding(self, concept: str, last_explanation: str, child_message: str) -> Tuple[UnderstandingState, str, str]:
        user_prompt = (
            f"Concept: {concept}\n"
            f"Last Explanation Given: {last_explanation}\n"
            f"Child's Response: {child_message}\n\n"
            "Analyze the child's response and provide the classification in JSON."
        )
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_text = await openai_service.get_chat_completion(
                messages, 
                temperature=0, 
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response_text)
            state_str = data.get("state", "confused")
            # Ensure the state is valid
            if state_str not in [s.value for s in UnderstandingState]:
                logger.warning(f"Invalid state '{state_str}' returned by evaluator. Defaulting to 'confused'.")
                state_str = "confused"
                
            state = UnderstandingState(state_str)
            reasoning = data.get("reasoning", "")
            hint = data.get("follow_up_hint", "")
            
            return state, reasoning, hint
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from evaluator agent: {e}. Content: {response_text}")
            return UnderstandingState.CONFUSED, "Error parsing evaluator response.", "Try asking the child to clarify their thought."
        except Exception as e:
            logger.error(f"Unexpected error in evaluator agent: {e}", exc_info=True)
            return UnderstandingState.CONFUSED, "Internal evaluator error.", "Continue the conversation normally."

evaluator_agent = EvaluatorAgent()

