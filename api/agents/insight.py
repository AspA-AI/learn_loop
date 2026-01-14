import json
import logging
from services.openai_service import openai_service
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class InsightAgent:
    def __init__(self):
        self.system_prompt = (
            "You are a supportive educational consultant for parents. "
            "Your job is to summarize a child's learning sessions into actionable insights.\n\n"
            "Respond strictly in JSON with these keys:\n"
            "- summary: A warm, 2-sentence summary of what the child explored.\n"
            "- achievements: A list of specific 'Aha!' moments or concepts they understood.\n"
            "- challenges: A list of concepts they found difficult or areas where they were confused.\n"
            "- recommended_next_steps: A list of 2-3 offline activities or conversation starters for the parent."
        )

    async def generate_parent_report(self, sessions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not sessions_data:
            return {
                "summary": "No learning sessions were recorded this week.",
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Start a new learning session to see progress!"]
            }

        try:
            user_prompt = f"Analyze the following learning session data and provide a report for the parent:\n\n{json.dumps(sessions_data)}"
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_text = await openai_service.get_chat_completion(
                messages, 
                temperature=0.7, 
                response_format={"type": "json_object"}
            )
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from insight agent: {e}. Content: {response_text}")
            return {
                "summary": "We encountered an error generating the detailed report.",
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Please try again later."]
            }
        except Exception as e:
            logger.error(f"Unexpected error in insight agent: {e}", exc_info=True)
            return {
                "summary": "An unexpected error occurred while analyzing the sessions.",
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Our team has been notified."]
            }

insight_agent = InsightAgent()

