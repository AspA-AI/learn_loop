from services.openai_service import openai_service
from models.schemas import AgeLevel
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ExplainerAgent:
    def __init__(self):
        self.role_description = (
            "You are a world-class educator specialized in child development for ages 6-10. "
            "Your goal is to explain academic concepts using age-appropriate framing and analogies."
        )
        
    def _get_system_prompt(self, age_level: int, concept: str, learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> str:
        """
        Returns age-adaptive system prompt with concept enforcement and language setting.
        """
        base_constraints = (
            "CRITICAL CONSTRAINTS:\n"
            f"- All communication MUST be entirely in {language}\n"
            "- You MUST stay focused ONLY on the concept: '{concept}'\n"
            "- Do NOT introduce other topics, concepts, or related subjects\n"
            "- Max 3 sentences per explanation\n"
            "- No complex jargon without an immediate analogy\n"
            "- All examples and explanations MUST relate to '{concept}' only"
        ).format(concept=concept)
        
        # Age context - let LLM use its knowledge of child development
        age_context = (
            f"You are explaining '{concept}' to a {age_level}-year-old child. "
            f"Adapt your language, examples, and explanation depth based on what a {age_level}-year-old would understand and find engaging. "
            f"Use your knowledge of child cognitive development for this age group."
        )
        
        # Learning profile context (if available)
        profile_context = ""
        if learning_profile:
            profile_instructions = []
            
            # Learning Style Adaptations
            if learning_profile.get("learning_style"):
                style = learning_profile["learning_style"].lower()
                if style == "visual":
                    profile_instructions.append(
                        "LEARNING STYLE: VISUAL\n"
                        "- Use visual symbols and emojis strategically (🔢, ➕, ➖, ✖️, ➗, 📊, 🎯)\n"
                        "- Use vivid visual descriptions: 'Imagine a number line stretching out...', 'Picture 3 groups of 4 apples...'\n"
                        "- Use spatial language: 'stack', 'arrange', 'organize', 'group', 'line up'\n"
                        "- Encourage visual imagination: 'Can you picture this in your mind?', 'What do you see when you think about...?'\n"
                        "- Use simple ASCII art for diagrams when helpful (e.g., arrays: ⬛⬛⬛⬛)\n"
                        "- Suggest drawing: 'Try drawing this out!', 'Can you sketch what this looks like?'\n"
                        "- DO NOT attempt to generate images or use image generation APIs"
                    )
                elif style == "auditory":
                    profile_instructions.append(
                        "LEARNING STYLE: AUDITORY\n"
                        "- Use rhythm, rhymes, and sound patterns in explanations\n"
                        "- Use sound-based analogies: 'It sounds like...', 'Listen to this pattern...'\n"
                        "- Encourage verbal repetition: 'Say it out loud with me...', 'Repeat after me...'\n"
                        "- Use musical or rhythmic language when appropriate\n"
                        "- Suggest reading explanations aloud\n"
                        "- Use onomatopoeia and sound effects in examples"
                    )
                elif style == "kinesthetic":
                    profile_instructions.append(
                        "LEARNING STYLE: KINESTHETIC\n"
                        "- Suggest physical activities: 'Try this with your hands...', 'Can you act this out?'\n"
                        "- Use movement-based analogies: 'Imagine you're jumping...', 'Think about running...'\n"
                        "- Encourage hands-on practice: 'Use objects to show this...', 'Try building this...'\n"
                        "- Use body movements in explanations: 'Stand up and...', 'Move your arms to show...'\n"
                        "- Connect concepts to physical sensations and actions"
                    )
                elif style == "reading/writing":
                    profile_instructions.append(
                        "LEARNING STYLE: READING/WRITING\n"
                        "- Encourage note-taking: 'Write this down...', 'Jot this in your own words...'\n"
                        "- Use written exercises: 'Try writing out...', 'Put this in a sentence...'\n"
                        "- Provide clear written explanations with structured text\n"
                        "- Use lists, bullet points, and organized text formats\n"
                        "- Encourage reading explanations carefully and writing responses"
                    )
            
            # Attention Span Adaptations
            if learning_profile.get("attention_span"):
                span = learning_profile["attention_span"].lower()
                if span == "short":
                    profile_instructions.append(
                        "ATTENTION SPAN: SHORT\n"
                        "- Keep ALL explanations under 50 words (2-3 sentences maximum)\n"
                        "- Break concepts into tiny, digestible chunks\n"
                        "- Check understanding every 2 messages: 'Got it so far?', 'Still with me?'\n"
                        "- Use quick transitions: move fast between ideas\n"
                        "- After 3-4 exchanges, proactively suggest: 'Want to take a quick break, or keep going?'\n"
                        "- Use very brief examples and keep questions short"
                    )
                elif span == "medium":
                    profile_instructions.append(
                        "ATTENTION SPAN: MEDIUM\n"
                        "- Keep explanations to 3-4 sentences (50-75 words)\n"
                        "- Check understanding every 3-4 messages\n"
                        "- Break concepts into moderate chunks\n"
                        "- After 5-6 exchanges, offer optional break: 'Doing great! Want to continue or take a moment?'"
                    )
                elif span == "long":
                    profile_instructions.append(
                        "ATTENTION SPAN: LONG\n"
                        "- Can provide more detailed explanations (4-6 sentences, 75-100 words)\n"
                        "- Can go deeper into concepts without frequent breaks\n"
                        "- Check understanding every 5-6 messages\n"
                        "- Can explore concepts more thoroughly"
                    )
            
            # Reading Level Adaptations
            if learning_profile.get("reading_level"):
                level = learning_profile["reading_level"].lower()
                if level == "beginner":
                    profile_instructions.append(
                        "READING LEVEL: BEGINNER\n"
                        "- Use simple, common words only\n"
                        "- Keep sentences short (5-8 words max)\n"
                        "- Avoid complex vocabulary - use everyday language\n"
                        "- Use simple sentence structures\n"
                        "- Define any necessary technical terms immediately with simple words"
                    )
                elif level == "intermediate":
                    profile_instructions.append(
                        "READING LEVEL: INTERMEDIATE\n"
                        "- Use age-appropriate vocabulary\n"
                        "- Sentences can be moderate length (8-12 words)\n"
                        "- Can introduce some new words with context clues\n"
                        "- Use varied sentence structures"
                    )
                elif level == "advanced":
                    profile_instructions.append(
                        "READING LEVEL: ADVANCED\n"
                        "- Can use richer, more sophisticated vocabulary\n"
                        "- Can use longer, more complex sentences (12+ words)\n"
                        "- Can explore nuanced concepts with appropriate language\n"
                        "- Can use varied and complex sentence structures"
                    )
            
            # Interests Integration
            if learning_profile.get("interests"):
                interests = learning_profile["interests"]
                if isinstance(interests, list):
                    interests_str = ", ".join(interests)
                else:
                    interests_str = str(interests)
                profile_instructions.append(
                    f"CHILD'S INTERESTS: {interests_str}\n"
                    "- Incorporate these interests into examples and analogies\n"
                    "- Use these topics to make explanations more engaging\n"
                    "- Connect the concept to their interests: 'Remember how you like {interests_str}? Let's use that to understand...'\n"
                    "- Personalize story explanations around these interests when possible"
                )
            
            # Strengths Integration
            if learning_profile.get("strengths"):
                strengths = learning_profile["strengths"]
                if isinstance(strengths, list):
                    strengths_str = ", ".join(strengths)
                else:
                    strengths_str = str(strengths)
                profile_instructions.append(
                    f"CHILD'S STRENGTHS: {strengths_str}\n"
                    "- Reference these strengths to build confidence: 'You're great at {strengths_str}, so let's use that skill here...'\n"
                    "- Use strengths as bridges to new concepts\n"
                    "- Provide positive reinforcement when they demonstrate these strengths\n"
                    "- Connect new learning to their existing strengths"
                )
            
            if profile_instructions:
                profile_context = "\n\n" + "="*50 + "\nPERSONALIZATION INSTRUCTIONS\n" + "="*50 + "\n"
                profile_context += "\n\n".join(profile_instructions)
                profile_context += "\n\nIMPORTANT: These personalization guidelines are MANDATORY. Apply them consistently throughout all explanations, questions, and interactions.\n"
            
        return f"{self.role_description}\n\n{base_constraints}\n\n{age_context}{profile_context}"

    async def get_initial_explanation(self, concept: str, age_level: int, child_name: str = "there", grounding_context: Optional[str] = None, learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> str:
        """
        Returns the initial greeting and readiness check.
        Structure: Greeting → Ask if ready → Wait for confirmation
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        user_prompt = (
            f"Greet {child_name} warmly and ask if they're ready to start learning about '{concept}'. "
            f"Be friendly and encouraging. Keep it short - just 2-3 sentences. "
            f"Adapt your language to be appropriate for a {age_level}-year-old child. "
            f"Example structure: 'Hey {child_name}! How are you today? Are you ready to learn about {concept}? "
            f"When you're ready, just let me know and we'll start!'"
        )
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await openai_service.get_chat_completion(messages, temperature=0.7)
    
    async def get_story_explanation(self, concept: str, age_level: int, child_name: str = "there", grounding_context: Optional[str] = None, learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> str:
        """
        Step 1: Explain using story/analogy only (works for ANY academic subject)
        Structure: Story explanation → Story-based quiz question
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        user_prompt = (
            f"Great! Now let's start learning about '{concept}'. "
            f"Explain '{concept}' to {child_name} (a {age_level}-year-old) using a fun, age-appropriate story or analogy. "
            f"Adapt your language and examples to what a {age_level}-year-old would understand and find engaging. "
            f"Keep it to 2-3 sentences. Focus ONLY on the story/analogy - do NOT mention academic notation, formulas, or technical terms yet. "
            f"After the story, give them a simple story-based question or problem to solve related to '{concept}'. "
            f"The question should test their understanding of the story/analogy you just explained. "
            f"Remember: Stay focused ONLY on '{concept}'. Do not introduce other topics."
        )
        
        if grounding_context:
            user_prompt += f"\n\nUse this specific curriculum context to inform your explanation: {grounding_context}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await openai_service.get_chat_completion(messages, temperature=0.7)
    
    async def get_academic_explanation(self, concept: str, age_level: int, child_name: str = "there", story_explanation: str = "", grounding_context: Optional[str] = None, learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> str:
        """
        Step 2: Connect story to academic/formal explanation (works for ANY academic subject)
        Structure: Connect story → Show academic notation/terminology → Explain symbols/terms
        For math: shows notation (10 - 3 = 7)
        For English: shows grammar rules, sentence structure
        For geography: shows maps, coordinates, terminology
        For science: shows formulas, scientific terms
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        # Unified prompt - LLM will automatically determine the appropriate academic format based on the concept
        user_prompt = (
            f"Now connect the story about '{concept}' to how we explain it academically! "
            f"Show {child_name} (a {age_level}-year-old) the proper academic way to understand '{concept}'. "
            f"This could be mathematical notation, grammar rules, scientific terms, geographical concepts, or any other academic format appropriate for '{concept}'. "
            f"Adapt the depth and terminology to what a {age_level}-year-old would understand. "
            f"Connect it directly to the story we just told about '{concept}'. "
            f"Remember: Stay focused ONLY on '{concept}'. Do not introduce other topics or related concepts."
        )
        
        # Include story context if available
        if story_explanation:
            user_prompt += f"\n\nRemember: The story we told was: {story_explanation[:200]}... Connect the academic explanation to this story."
        
        if grounding_context:
            user_prompt += f"\n\nUse this curriculum context: {grounding_context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await openai_service.get_chat_completion(messages, temperature=0.7)
    
    async def get_academic_quiz(self, concept: str, age_level: int, child_name: str = "there", learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> str:
        """
        Step 3: Quiz them on academic notation/terminology (works for ANY academic subject)
        Structure: Give problem/question using academic notation/terminology
        LLM automatically determines the appropriate format based on the concept.
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        # Unified prompt - LLM will automatically determine the appropriate quiz format
        user_prompt = (
            f"Now give {child_name} (a {age_level}-year-old) a simple question or problem about '{concept}' using the academic format we just learned. "
            f"The question should test their understanding of '{concept}' using the proper academic notation, terminology, rules, or structure appropriate for '{concept}'. "
            f"Adapt the difficulty to what a {age_level}-year-old would be able to solve or answer. "
            f"Keep it friendly and encouraging. This helps us see if they understand the academic way of expressing '{concept}'. "
            f"Remember: The question MUST be about '{concept}' only. Do not introduce other topics or related concepts."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await openai_service.get_chat_completion(messages, temperature=0.7)

    async def get_adaptive_response(
        self, 
        concept: str, 
        age_level: int, 
        child_message: str, 
        history: List[Dict[str, str]], 
        grounding_context: Optional[str] = None,
        understanding_state: Optional[str] = None,
        confusion_attempts: int = 0,
        learning_profile: Optional[Dict[str, Any]] = None,
        language: str = "English"
    ) -> tuple:
        """
        Returns (response, can_end_session, should_offer_end)
        - can_end_session: True if child has demonstrated full understanding
        - should_offer_end: True if child is stuck after multiple attempts (offer to end session)
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        # Add guidance for assessing understanding (works for ANY academic subject)
        system_prompt += (
            f"\n\nIMPORTANT: You are teaching '{concept}'. You need to assess understanding in TWO ways:\n"
            f"1. Story/Conceptual Understanding: Can they understand '{concept}' using the story/analogy?\n"
            f"2. Academic Understanding: Can they understand '{concept}' using the proper academic format (notation, terminology, rules, or structure appropriate for '{concept}')?\n\n"
            f"If the child answers a story-based question correctly but struggles with the academic way, "
            f"this is valuable information. Help them bridge the gap by connecting the story to the academic format. "
            f"If they do better with stories than academic format, note this - it shows they understand "
            f"the concept but need more practice with the academic way of expressing '{concept}'.\n\n"
            f"CRITICAL: Stay focused ONLY on '{concept}'. Do NOT introduce other topics or related concepts."
        )
        
        # Add guidance based on understanding state
        if understanding_state == "understood":
            system_prompt += (
                f"\n\nThe child has demonstrated understanding. However, do NOT immediately conclude they've mastered it. "
                f"Ask them to demonstrate their understanding by:\n"
                f"- Explaining '{concept}' in their own words\n"
                f"- Solving a simple problem or question (both with the story AND with the academic format for '{concept}')\n"
                f"- Giving their own example\n"
                f"Only after they provide substantive evidence should you acknowledge mastery."
            )
        elif understanding_state == "partial":
            system_prompt += (
                "\n\nThe child has partial understanding. Encourage them to:\n"
                "- Explain what they understand so far\n"
                "- Try solving a simple problem\n"
                "- Ask questions about what's confusing them\n"
                "Do NOT jump to conclusions - help them build on what they know."
            )
        elif understanding_state == "confused":
            if confusion_attempts >= 3:
                system_prompt += (
                    "\n\nIMPORTANT: The child has been confused for multiple attempts (3+). "
                    "It's okay if they're struggling. Offer them the option to end the session gracefully, "
                    "and reassure them that learning takes time. Say something like: "
                    "'Sometimes concepts take time to understand, and that's perfectly okay! Would you like to take a break and try again later?'"
                )
            else:
                system_prompt += (
                    "\n\nThe child is confused. Try a different approach:\n"
                    "- Use a simpler analogy\n"
                    "- Break it down into smaller steps\n"
                    "- Ask what specifically is confusing them\n"
                    "Be patient and encouraging."
                )
        elif understanding_state == "procedural":
            system_prompt += (
                "\n\nThe child's message is procedural (ready, thanks, ok). "
                "Acknowledge their response warmly and proceed with the next step of your explanation or ask your next question."
            )
        
        messages = [{"role": "system", "content": system_prompt}]
        if grounding_context:
            messages.append({"role": "system", "content": f"Curriculum Context: {grounding_context}"})
            
        messages.extend(history)
        messages.append({"role": "user", "content": child_message})
        
        response = await openai_service.get_chat_completion(messages, temperature=0.7)
        
        # The session route will determine can_end_session based on understanding states
        # We just return whether to offer ending if confused
        should_offer_end = (understanding_state == "confused" and confusion_attempts >= 3)
        
        return response, False, should_offer_end  # can_end_session determined by session route
    
    async def generate_quiz_questions(self, concept: str, age_level: int, child_name: str = "there", num_questions: int = 5, learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> List[str]:
        """
        Generate a set of practice quiz questions for the concept.
        Returns a list of questions that test understanding of the concept.
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        user_prompt = (
            f"Generate {num_questions} practice questions about '{concept}' for a {age_level}-year-old child named {child_name}. "
            f"The questions should:\n"
            f"- Test understanding of '{concept}' at an age-appropriate level\n"
            f"- Mix story-based and academic format questions\n"
            f"- Be progressively challenging but achievable for a {age_level}-year-old\n"
            f"- Cover different aspects of '{concept}'\n"
            f"- Be clear and engaging\n\n"
            f"Return ONLY a JSON array of question strings, nothing else. "
            f"Example format: [\"Question 1\", \"Question 2\", \"Question 3\", ...]\n"
            f"Remember: All questions MUST be about '{concept}' only. Do not introduce other topics."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            import json
            response_text = await openai_service.get_chat_completion(
                messages, 
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            data = json.loads(response_text)
            # Handle both {"questions": [...]} and direct array formats
            if "questions" in data:
                return data["questions"][:num_questions]
            elif isinstance(data, list):
                return data[:num_questions]
            else:
                # Fallback: try to extract questions from any array field
                for key, value in data.items():
                    if isinstance(value, list):
                        return value[:num_questions]
                return []
        except Exception as e:
            logger.error(f"Error generating quiz questions: {e}")
            # Fallback: generate simple questions
            return [
                f"Can you explain '{concept}' in your own words?",
                f"Give an example of '{concept}'.",
                f"How would you use '{concept}' in a real situation?"
            ][:num_questions]
    
    async def evaluate_quiz_answer(self, concept: str, age_level: int, question: str, answer: str, learning_profile: Optional[Dict[str, Any]] = None, language: str = "English") -> Dict[str, Any]:
        """
        Evaluate a quiz answer and provide feedback.
        Returns: {"correct": bool, "feedback": str, "score": int}
        """
        system_prompt = self._get_system_prompt(age_level, concept, learning_profile, language)
        
        user_prompt = (
            f"Evaluate this answer to a quiz question about '{concept}':\n\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n\n"
            f"Provide:\n"
            f"- Whether the answer is correct (or partially correct)\n"
            f"- Encouraging feedback\n"
            f"- A score from 0-100\n\n"
            f"Return ONLY a JSON object with keys: 'correct' (boolean), 'feedback' (string), 'score' (integer 0-100). "
            f"Be encouraging and constructive. Remember: The question is about '{concept}' only."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            import json
            response_text = await openai_service.get_chat_completion(
                messages,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                response_format={"type": "json_object"}
            )
            data = json.loads(response_text)
            return {
                "correct": data.get("correct", False),
                "feedback": data.get("feedback", "Good try! Keep practicing."),
                "score": data.get("score", 50)
            }
        except Exception as e:
            logger.error(f"Error evaluating quiz answer: {e}")
            return {
                "correct": True,  # Default to lenient
                "feedback": "Good job! Keep practicing.",
                "score": 75
            }

    async def translate_concept(self, concept: str, target_language: str) -> str:
        """
        Translate a concept name into the target language.
        """
        if target_language == "English":
            return concept
            
        system_prompt = (
            "You are a helpful academic translator. "
            f"Translate the following educational concept into {target_language}. "
            "Return ONLY the translated name, nothing else."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": concept}
        ]
        
        return await openai_service.get_chat_completion(messages, temperature=0.1)

explainer_agent = ExplainerAgent()
