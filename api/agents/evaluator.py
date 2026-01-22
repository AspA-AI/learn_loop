import json
import logging
import os
from services.openai_service import openai_service
from models.schemas import UnderstandingState
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self):
        self.ground_truth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reporting_ground_truth.txt")
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

    def _get_ground_truth(self) -> str:
        """Read the reporting ground truth file"""
        try:
            with open(self.ground_truth_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading ground truth file: {e}")
            return "Conceptual Accuracy, Cognitive Confidence, Engagement & Persistence, Communication Expression. All scale 1-10."

    async def evaluate_understanding(self, concept: str, last_explanation: str, child_message: str, language: str = "English") -> Tuple[UnderstandingState, str, str, Dict[str, Any]]:
        """
        Returns: (state, reasoning, hint, performance_metrics)
        """
        user_prompt = (
            f"Language: {language}\n"
            f"Concept: {concept}\n"
            f"Last Explanation Given: {last_explanation}\n"
            f"Child's Response: {child_message}\n\n"
            f"Analyze the child's response for the given last explanation and provide the classification in JSON. "
            f"CRITICAL: All reasoning and hints MUST be in {language}."
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

    async def generate_session_report(self, child_name: str, concept: str, interactions: List[Dict[str, Any]], language: str = "English") -> Dict[str, Any]:
        """
        Generate a formal academic snapshot and metrics for a completed session.
        """
        ground_truth = self._get_ground_truth()
        
        # Prepare interaction history for the LLM
        history_text = "\n".join([
            f"{'Child' if i['role'] == 'user' else 'AI'}: {i['content']}"
            for i in interactions[-15:] # Only send the last 15 interactions to save tokens
        ])
        
        system_prompt = (
            "You are a professional educational assessor for a homeschooling program. "
            "Your task is to generate a formal academic snapshot and score the child's performance based on the following GROUND TRUTH standards:\n\n"
            f"{ground_truth}\n\n"
            f"CRITICAL: The 'summary' and 'reasoning' fields MUST be written entirely in {language}.\n\n"
            "Respond ONLY in JSON format with the following keys:\n"
            "- metrics: { accuracy: int, confidence: int, persistence: int, expression: int } (All 1-10)\n"
            "- summary: string (Exactly 3 sentences: What was learned, What was achieved, Future focus)\n"
            "- reasoning: string (Briefly explain the scores based on the conversation history)\n"
        )
        
        user_prompt = (
            f"Student Name: {child_name}\n"
            f"Topic: {concept}\n\n"
            "CONVERSATION HISTORY:\n"
            f"{history_text}\n\n"
            "Generate the formal metrics and 3-sentence summary."
        )
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_text = await openai_service.get_chat_completion(
                messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error generating session report: {e}", exc_info=True)
            return {
                "metrics": {"accuracy": 5, "confidence": 5, "persistence": 5, "expression": 5},
                "summary": f"The session covered {concept}. The student engaged with the material. More practice is recommended.",
                "reasoning": "Fallback report due to internal error."
            }
    
evaluator_agent = EvaluatorAgent()
