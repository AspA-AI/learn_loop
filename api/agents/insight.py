import json
import logging
from services.openai_service import openai_service
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class InsightAgent:
    def __init__(self):
        self.system_prompt = (
            "You are a supportive educational consultant for parents. "
            "Your job is to summarize a child's learning session into actionable insights.\n\n"
            "IMPORTANT: If this is a mathematical concept, analyze the conversation to identify:\n"
            "1. Story/Conceptual Understanding: Did the child answer story-based questions well? (e.g., 'If you have 8 cookies and eat 2, how many left?')\n"
            "2. Mathematical Operation Understanding: Did the child answer math notation questions well? (e.g., 'Can you solve 8 - 2 = ?')\n"
            "If the child did better with stories than math notation, this is a KEY INSIGHT - they understand the concept but need more practice with mathematical symbols.\n\n"
            "You MUST respond with a JSON object following this EXACT structure:\n"
            "{\n"
            '  "summary": "A warm, 2-3 sentence summary of what the child explored and learned.",\n'
            '  "achievements": ["Specific achievement 1", "Specific achievement 2", "Specific achievement 3"],\n'
            '  "challenges": ["Challenge or confusion area 1", "Challenge or confusion area 2"],\n'
            '  "recommended_next_steps": ["Next step 1", "Next step 2", "Next step 3"],\n'
            '  "key_insights": ["Insight about learning style", "Insight about engagement"],\n'
            '  "concept_mastery_level": "beginner" | "developing" | "proficient" | "mastered"\n'
            "}\n\n"
            "Requirements:\n"
            "- summary: 2-3 sentences, warm and encouraging. For math concepts, mention if they understand conceptually but need math notation practice.\n"
            "- achievements: Array of 2-5 specific things the child understood or did well\n"
            "- challenges: Array of 0-3 areas where the child struggled. For math, include if they struggle with mathematical notation vs. conceptual understanding.\n"
            "- recommended_next_steps: Array of 2-4 actionable steps for parents. For math, suggest practicing mathematical notation if needed.\n"
            "- key_insights: Array of 1-3 observations. MUST include story vs. math performance if it's a mathematical concept.\n"
            "- concept_mastery_level: One of: 'beginner', 'developing', 'proficient', 'mastered'\n"
            "All arrays must be present even if empty. Do not add extra fields."
        )
        
        self.standard_format = {
            "summary": "",
            "achievements": [],
            "challenges": [],
            "recommended_next_steps": [],
            "key_insights": [],
            "concept_mastery_level": "developing"
        }

    def _validate_and_normalize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure report matches standard format"""
        normalized = self.standard_format.copy()
        
        # Validate and set each field
        normalized["summary"] = str(report.get("summary", "")).strip()
        if not normalized["summary"]:
            normalized["summary"] = "The child engaged with the learning session."
        
        # Ensure arrays exist and are lists
        normalized["achievements"] = list(report.get("achievements", [])) if isinstance(report.get("achievements"), list) else []
        normalized["challenges"] = list(report.get("challenges", [])) if isinstance(report.get("challenges"), list) else []
        normalized["recommended_next_steps"] = list(report.get("recommended_next_steps", [])) if isinstance(report.get("recommended_next_steps"), list) else []
        normalized["key_insights"] = list(report.get("key_insights", [])) if isinstance(report.get("key_insights"), list) else []
        
        # Validate mastery level
        valid_levels = ["beginner", "developing", "proficient", "mastered"]
        mastery_level = str(report.get("concept_mastery_level", "developing")).lower()
        normalized["concept_mastery_level"] = mastery_level if mastery_level in valid_levels else "developing"
        
        return normalized

    async def generate_parent_report(self, sessions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not sessions_data:
            return {
                "summary": "No learning sessions were recorded.",
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Start a new learning session to see progress!"],
                "key_insights": [],
                "concept_mastery_level": "beginner"
            }

        try:
            user_prompt = (
                f"Analyze the following learning session data and provide a standardized evaluation report:\n\n"
                f"{json.dumps(sessions_data, indent=2)}\n\n"
                f"Remember to follow the EXACT JSON structure specified in the system prompt. "
                f"All fields must be present: summary, achievements, challenges, recommended_next_steps, key_insights, concept_mastery_level."
            )
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_text = await openai_service.get_chat_completion(
                messages, 
                temperature=0.7, 
                response_format={"type": "json_object"}
            )
            
            parsed_report = json.loads(response_text)
            # Validate and normalize to ensure consistent structure
            return self._validate_and_normalize_report(parsed_report)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from insight agent: {e}. Content: {response_text}")
            return {
                "summary": "We encountered an error generating the detailed report.",
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Please try again later."],
                "key_insights": [],
                "concept_mastery_level": "developing"
            }
        except Exception as e:
            logger.error(f"Unexpected error in insight agent: {e}", exc_info=True)
            return {
                "summary": "An unexpected error occurred while analyzing the sessions.",
                "achievements": [],
                "challenges": [],
                "recommended_next_steps": ["Our team has been notified."],
                "key_insights": [],
                "concept_mastery_level": "developing"
            }

insight_agent = InsightAgent()

