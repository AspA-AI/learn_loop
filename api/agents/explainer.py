from services.openai_service import openai_service
from models.schemas import AgeLevel
from typing import List, Dict, Optional

class ExplainerAgent:
    def __init__(self):
        self.role_description = (
            "You are a world-class educator specialized in child development for ages 6-10. "
            "Your goal is to explain academic concepts using age-appropriate framing and analogies."
        )
        
    def _get_system_prompt(self, age_level: AgeLevel) -> str:
        base_constraints = (
            "Constraints:\n"
            "- Max 3 sentences per explanation.\n"
            "- No complex jargon without an immediate analogy.\n"
            "- Stay strictly within the current topic."
        )
        
        framing = ""
        if age_level == AgeLevel.SIX:
            framing = (
                "Cognitive Framing (Age 6): Use 'Magical/Physical' framing. "
                "Focus on concrete sensory-based language and simple physical analogies. "
                "Example: 'The wind is like a big giant blowing on the trees.'"
            )
        elif age_level == AgeLevel.EIGHT:
            framing = (
                "Cognitive Framing (Age 8): Use 'Cause-and-Effect' framing. "
                "Focus on logical relationships and structured stories. "
                "Example: 'The wind moves because the air gets warm and wants to spread out.'"
            )
        elif age_level == AgeLevel.TEN:
            framing = (
                "Cognitive Framing (Age 10): Use 'Systemic/Scientific' framing. "
                "Focus on conceptual models and abstract comparisons. "
                "Example: 'Wind is caused by differences in air pressure between warm and cold areas.'"
            )
            
        return f"{self.role_description}\n\n{base_constraints}\n\n{framing}"

    async def get_initial_explanation(self, concept: str, age_level: AgeLevel, child_name: str = "there", grounding_context: Optional[str] = None, context_overrides: Optional[dict] = None) -> str:
        system_prompt = self._get_system_prompt(age_level)
        
        user_prompt = (
            f"Start by greeting {child_name} warmly. "
            f"Then, explain the concept of '{concept}' to them using a fun, {age_level}-year-old appropriate analogy. "
            "Keep it under 3 sentences."
        )

        if grounding_context:
            user_prompt += f"\n\nUse this specific curriculum context for your explanation: {grounding_context}"
        
        if context_overrides and "interests" in context_overrides:
            interests = ", ".join(context_overrides["interests"])
            user_prompt += f" Try to use analogies related to: {interests}."
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await openai_service.get_chat_completion(messages, temperature=0.7)

    async def get_adaptive_response(self, concept: str, age_level: AgeLevel, child_message: str, history: List[Dict[str, str]], grounding_context: Optional[str] = None) -> str:
        system_prompt = self._get_system_prompt(age_level)
        
        messages = [{"role": "system", "content": system_prompt}]
        if grounding_context:
            messages.append({"role": "system", "content": f"Curriculum Context: {grounding_context}"})
            
        messages.extend(history)
        messages.append({"role": "user", "content": child_message})
        
        return await openai_service.get_chat_completion(messages, temperature=0.7)

explainer_agent = ExplainerAgent()
