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

    async def evaluate_answers(
        self,
        concept: str,
        interactions: List[Dict[str, Any]],
        language: str = "English",
    ) -> Dict[str, Any]:
        """
        End-of-session, evidence-based grading of individual question/answer pairs.
        Returns JSON with per-question scores, without computing an overall percentage.
        Shape:
        {
          "questions": [
            {
              "id": int,
              "question": str,
              "child_answer": str,
              "answer_relevance": int (0-100),
              "answer_correctness": int (0-100),
              "notes": str
            }, ...
          ],
          "topic_discussed": bool,
          "notes": str
        }
        """
        try:
            # Bound history length for token efficiency
            convo_lines: List[str] = []
            for i in interactions[-30:]:
                role = "Child" if i.get("role") == "user" else "AI"
                text = str(i.get("content") or "").strip()
                if text:
                    convo_lines.append(f"{role}: {text}")
            history_text = "\n".join(convo_lines)

            system = (
                "You are an educational evaluator. Your task is to grade how well the child answered each "
                "concept-related question in the conversation.\n\n"
                "CRITICAL RULE: ONLY evaluate questions that have answers. Skip any questions where:\n"
                "- The child did not respond\n"
                "- The child's response is empty or just whitespace\n"
                "- The child's response is clearly not an answer (e.g., 'I don't know', 'skip', 'pass')\n"
                "- The child only said acknowledgments like 'ready', 'Ready!', 'yes', 'ok', 'okay', 'sure' - these are NOT concept answers\n"
                "- The conversation moved on without the child answering\n\n"
                "Rules:\n"
                "- First, identify the main concept the AI is teaching (it is provided explicitly).\n"
                "- Then, scan the conversation for AI QUESTIONS about that concept and the child's direct replies.\n"
                "- ONLY consider question/answer pairs where:\n"
                "  1. The AI asked a question about the concept (NOT setup like 'Are you ready?', 'Ready to start?')\n"
                "  2. The child provided an actual substantive answer about the concept (NOT 'ready', 'yes', 'ok' - those are acknowledgments)\n"
                "  3. The question/answer pair is truly about the concept (ignore greetings, 'are you ready?', chit-chat)\n"
                "- DO NOT create entries for questions that were not answered - skip them entirely.\n"
                "- CRITICAL: child_answer MUST be the child's EXACT words from the conversation. Do NOT invent, paraphrase, or add words the child never said.\n"
                "- For each valid answered pair, create one entry with:\n"
                "  * id: sequential integer starting from 1\n"
                "  * question: the AI's question (shortened if very long)\n"
                "  * child_answer: the child's exact answer text as it appears in the conversation (copy-paste, do not embellish)\n"
                "  * answer_relevance: 0-100, how much the child's answer actually addresses and engages with the question about the concept.\n"
                "    CRITICAL: If the answer is completely wrong, nonsensical, or shows no understanding (e.g., answering '0' to all addition questions), "
                "    the relevance should be LOW (0-30), not high. High relevance (70-100) means the child is meaningfully engaging with the question, "
                "    even if partially incorrect. Low relevance means the answer doesn't meaningfully address what was asked.\n"
                "  * answer_correctness: 0-100, how mathematically/academically correct the answer is for the concept.\n"
                "    If the answer is completely wrong, this should be 0-20. If partially correct, 30-70. If fully correct, 80-100.\n"
                "  * notes: very short justification for the scores\n"
                "- Use the full 0-100 range, but be consistent: 100 = fully relevant/correct, 0 = completely off/nonsensical.\n"
                "- IMPORTANT: answer_relevance and answer_correctness should generally align. If correctness is very low (0-20), "
                "    relevance should also be low (0-40) unless the child is clearly trying to engage but misunderstanding.\n"
                "- topic_discussed is true if there is at least one question/answer pair with relevance >= 50, otherwise false.\n"
                "- Limit to at most 12 question entries to keep the JSON small.\n"
                f"- All free-text fields (notes) MUST be written entirely in {language}.\n\n"
                "Respond ONLY as JSON with keys: questions (array), topic_discussed (bool), notes (string)."
            )

            user = (
                f"Concept: {concept}\n"
                f"Conversation history (AI and child):\n{history_text}\n\n"
                "Extract and grade the concept-related question/answer pairs as described."
            )

            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]

            response_text = await openai_service.get_chat_completion(
                messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(response_text or "{}")

            questions = data.get("questions", [])
            if not isinstance(questions, list):
                questions = []

            logger.info(f"📋 [EVALUATOR] LLM returned {len(questions)} raw question/answer pairs for concept '{concept}'")

            # Build actual child messages from conversation - reject LLM hallucinations (answers not in conversation)
            def _normalize_for_substring(s: str) -> str:
                return "".join(c for c in s.lower() if c.isalnum() or c.isspace()).strip()
            user_messages = [str(i.get("content") or "").strip() for i in interactions if i.get("role") == "user"]
            user_messages_normalized = _normalize_for_substring(" ".join(user_messages))

            # Questions that are setup/greeting, NOT concept-related - exclude from grading
            setup_question_indicators = ["ready", "ready to", "start", "begin", "would you like", "shall we", "let's begin"]
            # Answers that are just acknowledgments, not substantive concept answers (strip punctuation for match: "Ready!" -> "ready")
            acknowledgment_answers = ["ready", "yes", "ok", "okay", "yeah", "yep", "sure", "let's go", "yea", "nod", "yup"]

            def _normalize_for_ack_check(s: str) -> str:
                """Strip punctuation so 'Ready!' matches 'ready'."""
                return "".join(c for c in s.lower().strip() if c.isalnum() or c.isspace()).strip()

            cleaned_questions: List[Dict[str, Any]] = []
            for idx, q in enumerate(questions, start=1):
                if not isinstance(q, dict):
                    continue
                question_text = str(q.get("question") or "").strip()
                answer_text = str(q.get("child_answer") or "").strip()
                
                # Skip if question or answer is missing
                if not question_text or not answer_text:
                    logger.debug(f"📋 [EVALUATOR] Skipped pair {idx}: empty question or answer")
                    continue
                
                # Skip setup/greeting questions (e.g. "Are you ready?", "Ready to start?")
                question_lower = question_text.lower()
                if any(ind in question_lower for ind in setup_question_indicators):
                    logger.info(f"📋 [EVALUATOR] Skipped pair {idx} (setup question): Q={question_text[:50]}... A={answer_text[:30]}")
                    continue
                
                # Skip answers that are just acknowledgments - normalize first so "Ready!" matches "ready"
                answer_normalized = _normalize_for_ack_check(answer_text)
                if answer_normalized in acknowledgment_answers:
                    logger.info(f"📋 [EVALUATOR] Skipped pair {idx} (acknowledgment answer): Q={question_text[:50]}... A={answer_text!r}")
                    continue
                
                # Skip if answer indicates no answer was given
                answer_lower = answer_text.lower().strip()
                skip_indicators = ["i don't know", "i don't know.", "don't know", "skip", "pass", "no answer", 
                                  "n/a", "na", "none", "nothing", "idk"]
                if any(indicator in answer_lower for indicator in skip_indicators):
                    continue

                # CRITICAL: Reject LLM hallucinations - child_answer must appear in actual conversation
                answer_norm = _normalize_for_substring(answer_text)
                if not answer_norm or answer_norm not in user_messages_normalized:
                    logger.info(f"📋 [EVALUATOR] Skipped pair {idx} (answer not in conversation - hallucination): A={answer_text!r}")
                    continue

                try:
                    rel = float(q.get("answer_relevance", 0) or 0)
                except Exception:
                    rel = 0.0
                try:
                    corr = float(q.get("answer_correctness", 0) or 0)
                except Exception:
                    corr = 0.0
                notes = str(q.get("notes") or "").strip()
                cleaned_questions.append(
                    {
                        "id": idx,
                        "question": question_text,
                        "child_answer": answer_text,
                        "answer_relevance": max(0, min(100, int(round(rel)))),
                        "answer_correctness": max(0, min(100, int(round(corr)))),
                        "notes": notes,
                    }
                )
            cleaned_questions = cleaned_questions[:12]

            logger.info(f"📋 [EVALUATOR] After filtering: {len(cleaned_questions)} valid concept Q/A pairs kept")
            for q in cleaned_questions:
                logger.info(f"   -> Q: {q.get('question', '')[:60]}... A: {q.get('child_answer', '')[:40]} (rel={q.get('answer_relevance')}, corr={q.get('answer_correctness')})")

            topic_discussed = bool(
                any(q.get("answer_relevance", 0) >= 50 for q in cleaned_questions)
            )
            notes = str(data.get("notes") or "").strip()

            return {
                "questions": cleaned_questions,
                "topic_discussed": topic_discussed,
                "notes": notes,
            }
        except Exception as e:
            logger.warning(f"Error in evaluate_answers: {e}", exc_info=True)
            return {"questions": [], "topic_discussed": False, "notes": ""}

evaluator_agent = EvaluatorAgent()
