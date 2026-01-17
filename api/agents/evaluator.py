import json
import logging
from services.openai_service import openai_service
from models.schemas import UnderstandingState
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self):
        self.system_prompt = (
            "You are an expert educational evaluator. Your job is to determine if a child understands a concept based on their message.\n\n"
            "CRITICAL CONTEXT CHECK:\n"
            "1. First, look at the AI's Last Message/Question. Did the AI actually ask a question about the topic or explain something technical?\n"
            "2. If the AI just asked 'Are you ready?', 'Do you want to continue?', 'Do you want a quiz?', or said 'Hello', then any response (yes, ok, ready, hi) is 'procedural'.\n"
            "3. ONLY if the AI asked a substantive question about the topic should you look for 'understood', 'partial', or 'confused'.\n\n"
            "UNDERSTANDING STATES:\n"
            "1. 'understood': The child demonstrates a clear grasp of the concept or correctly answers a question about it.\n"
            "2. 'partial': The child has some idea but is missing key details or shows slight hesitation.\n"
            "3. 'confused': The child expresses frustration, says they don't understand, or gives a fundamentally incorrect answer to a topic-related question.\n"
            "4. 'procedural': The response is conversational or procedural, OR the AI's last message was not an academic question. Examples: 'ready', 'yes', 'ok', 'thanks', 'hello', 'i'm set'.\n\n"
            "Respond ONLY in JSON format with the following keys:\n"
            "- state: one of 'understood', 'partial', 'confused', 'procedural'\n"
            "- reasoning: a brief explanation of why you chose this state\n"
            "- follow_up_hint: a gentle, encouraging hint to help them understand if they are partial/confused. Otherwise, null.\n"
        )

    async def evaluate_understanding(self, concept: str, last_explanation: str, child_message: str) -> Tuple[UnderstandingState, str, str, Dict[str, Any]]:
        """
        Returns: (state, reasoning, hint, performance_metrics)
        """
        
        
        user_prompt = (
            f"Concept: {concept}\n"
            f"Last Explanation Given: {last_explanation}\n"
            f"Child's Response: {child_message}\n\n"
            "Analyze the child's response for the given last explanation and provide the classification in JSON."
        )
        
        performance_metrics = {}
        
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
                        
            return state, reasoning, hint, performance_metrics
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from evaluator agent: {e}. Content: {response_text}")
            return UnderstandingState.CONFUSED, "Error parsing evaluator response.", "Try asking the child to clarify their thought.", {}
        except Exception as e:
            logger.error(f"Unexpected error in evaluator agent: {e}", exc_info=True)
            return UnderstandingState.CONFUSED, "Internal evaluator error.", "Continue the conversation normally.", {}
    
evaluator_agent = EvaluatorAgent()

