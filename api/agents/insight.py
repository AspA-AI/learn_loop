import json
import logging
import os
from datetime import datetime
from services.openai_service import openai_service
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class InsightAgent:
    def __init__(self):
        self.ground_truth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reporting_ground_truth.txt")
        self.system_prompt = (
            "You are a supportive educational consultant for parents. "
            "Your job is to summarize a child's learning session into actionable insights.\n\n"
            "CRITICAL EVIDENCE RULES (do not violate):\n"
            "- Only state what is supported by the transcript/session data.\n"
            "- Do NOT assume the child 'enjoyed' the story, was 'engaged', or 'participated actively' unless the child explicitly expresses it.\n"
            "- If the session is short or ends early, you MUST be cautious and say evidence is limited.\n"
            "- Prefer neutral, observable statements like: 'was introduced to...', 'attempted one question...', 'answered incorrectly...', 'ended early'.\n\n"
            "DEFINITION OF 'ACHIEVEMENTS' (important):\n"
            "- Achievements must reflect what the CHILD demonstrated (e.g., correct answers, clear explanations, persistence), NOT what the AI presented.\n"
            "- If the child did not provide enough substantive responses to demonstrate learning (early end / no answers), then achievements MUST be an empty array [].\n\n"
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

    def _get_ground_truth(self) -> str:
        """Read the reporting ground truth file"""
        try:
            with open(self.ground_truth_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading ground truth file: {e}")
            return "Conceptual Accuracy, Cognitive Confidence, Engagement & Persistence, Communication Expression. All scale 1-10."

    def _validate_and_normalize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure report matches standard format"""
        normalized = self.standard_format.copy()
        
        # Validate and set each field
        normalized["summary"] = str(report.get("summary", "")).strip()
        if not normalized["summary"]:
            normalized["summary"] = "A learning session was recorded."
        
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
            # Compute lightweight evidence signals to discourage overconfident claims on short sessions
            # sessions_data is a list, but in our usage it's typically a single session snapshot.
            interactions: List[Dict[str, Any]] = []
            try:
                interactions = (sessions_data[0] or {}).get("interactions", []) if sessions_data else []
            except Exception:
                interactions = []

            user_texts = []
            for i in interactions:
                if i.get("role") == "user" and i.get("content") is not None:
                    user_texts.append(str(i.get("content")).strip())

            procedural = {"ready", "ok", "okay", "yes", "yep", "yeah", "sure", "start", "let's go", "lets go"}
            substantive_user = [
                u for u in user_texts
                if u and u.lower() not in procedural and len(u) > 1
            ]
            limited_evidence = len(substantive_user) < 2

            user_prompt = (
                f"Analyze the following learning session data and provide a standardized evaluation report:\n\n"
                f"{json.dumps(sessions_data, indent=2)}\n\n"
                f"EVIDENCE SIGNALS:\n"
                f"- total_user_messages: {len(user_texts)}\n"
                f"- substantive_user_messages: {len(substantive_user)}\n"
                f"- limited_evidence: {limited_evidence}\n\n"
                f"If limited_evidence is true, you MUST avoid claims about enjoyment/engagement/active participation. "
                f"In that case, achievements MUST be an empty array []. "
                f"Also include in key_insights that evidence is limited because the session ended early.\n\n"
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
            normalized = self._validate_and_normalize_report(parsed_report)

            # Enforce achievement semantics: achievements are what the child demonstrated.
            # If limited evidence, force achievements to be empty.
            if limited_evidence:
                normalized["achievements"] = []
                # Encourage a conservative mastery level in early-ended sessions
                if normalized.get("concept_mastery_level") in ["proficient", "mastered"]:
                    normalized["concept_mastery_level"] = "beginner"
                # Ensure the report notes limited evidence somewhere
                if not any("limited" in str(x).lower() for x in (normalized.get("key_insights") or [])):
                    normalized["key_insights"] = ["Limited evidence due to early session end."] + (normalized.get("key_insights") or [])

            return normalized
            
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

    async def generate_formal_periodic_report(self, child_info: Dict[str, Any], parent_info: Dict[str, Any], sessions: List[Dict[str, Any]], curriculum_info: str, report_type: str) -> Dict[str, Any]:
        """
        Generate a professional, inspector-ready progress report.
        """
        ground_truth = self._get_ground_truth()
        current_year = datetime.now().year
        
        # Aggregate session summaries and metrics
        session_summaries = []
        avg_metrics = {"accuracy": 0, "confidence": 0, "persistence": 0, "expression": 0}
        total_sessions = len(sessions)
        
        for s in sessions:
            if s.get("academic_summary"):
                session_summaries.append(f"- Topic: {s['concept']}: {s['academic_summary']}")
            
            metrics = s.get("metrics") or {}
            for k in avg_metrics:
                avg_metrics[k] += metrics.get(k, 5)
        
        if total_sessions > 0:
            for k in avg_metrics:
                avg_metrics[k] = round(avg_metrics[k] / total_sessions, 1)
        
        system_prompt = (
            "You are a professional educational assessor generating a formal progress report for a homeschooling inspector. "
            "Your report must be formal, objective, and evidence-based. "
            "\n\nSTYLING RULES:\n"
            "1. Use [H1] text [/H1] for main section headings.\n"
            "2. Use [H2] text [/H2] for subheadings.\n"
            "3. Use **text** for bold emphasis.\n"
            "4. Do NOT use # symbols.\n\n"
            "Structure your report into these EXACT sections in this order:\n\n"
            "1. STUDENT & PROGRAM IDENTIFICATION\n"
            "Student Name: [Name]\n"
            "Student Age: [Age]\n"
            "Parent/Guardian: [Name]\n"
            "Curriculum Name: [Name]\n"
            "Academic Year: [Year]\n\n"
            "2. EVALUATION METHODOLOGY & METRIC DEFINITIONS\n"
            "The following metrics are used to evaluate student performance on a scale of 1 to 10:\n"
            "CONCEPTUAL ACCURACY: The degree to which the student's responses align with factual and logical requirements.\n"
            "COGNITIVE CONFIDENCE: The certainty and speed displayed in responses, measuring the transition from guessing to knowing.\n"
            "ENGAGEMENT AND PERSISTENCE: The student's willingness to tackle challenges and stay focused on objectives.\n"
            "COMMUNICATION EXPRESSION: The ability to articulate thoughts clearly and explain concepts in the student's own words.\n\n"
            "3. EXECUTIVE SUMMARY\n"
            "A high-level overview of the student's progress during this period.\n\n"
            "4. CURRICULUM COVERED\n"
            "Detail the specific topics and concepts explored, explicitly referencing the curriculum name provided.\n\n"
            "5. PROGRESS MATRIX ANALYSIS\n"
            "Discuss the 4 metrics above using evidence from the sessions. Mention growth deltas if visible.\n\n"
            "6. AREAS OF STRENGTH\n"
            "Highlight where the student excelled.\n\n"
            "7. AREAS FOR DEVELOPMENT\n"
            "Objective discussion of challenges and next steps.\n\n"
            "Respond ONLY in JSON format with the following keys:\n"
            "- identification: string (Section 1 content)\n"
            "- methodology: string (Section 2 content)\n"
            "- narrative: string (Sections 3-7 content)\n"
            "- metrics_summary: { accuracy: float, confidence: float, persistence: float, expression: float }\n"
            "- recommendation: string (A 1-sentence final recommendation)"
        )
        
        user_prompt = (
            f"STUDENT: {child_info['name']} (Age: {child_info['age_level']})\n"
            f"PARENT/GUARDIAN: {parent_info.get('name', 'Parent')}\n"
            f"CURRICULUM: {curriculum_info}\n"
            f"ACADEMIC YEAR: {current_year}\n"
            f"REPORT TYPE: {report_type.capitalize()}\n"
            f"SESSIONS CONDUCTED: {total_sessions}\n\n"
            "AGGREGATED SESSION SUMMARIES:\n"
            + "\n".join(session_summaries) + "\n\n"
            f"AGGREGATED METRICS: {json.dumps(avg_metrics)}\n\n"
            "Write the formal report components."
        )
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_text = await openai_service.get_chat_completion(
                messages,
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            res_data = json.loads(response_text)
            
            # Combine components for legacy storage if needed, but we'll return the structured data
            # We'll save the combined content to the database 'content' field
            combined_content = json.dumps({
                "identification": res_data.get("identification", ""),
                "methodology": res_data.get("methodology", ""),
                "narrative": res_data.get("narrative", "")
            })
            
            return {
                "content": combined_content,
                "metrics_summary": res_data.get("metrics_summary", avg_metrics),
                "recommendation": res_data.get("recommendation", "Manual review required.")
            }
        except Exception as e:
            logger.error(f"Error generating formal report: {e}", exc_info=True)
            return {
                "content": f"# Progress Report: {child_info['name']}\n\nError generating detailed report. Please try again.",
                "metrics_summary": avg_metrics,
                "recommendation": "Manual review required."
            }

    async def translate_report(self, report_content: str, target_language: str) -> str:
        """
        Translate a formal report's narrative content into the target language on the fly.
        """
        system_prompt = (
            "You are a professional academic translator. "
            f"Your task is to translate the following academic progress report into {target_language}.\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "- Maintain the professional, formal, and objective tone of the original.\n"
            "- Preserve the exact structure and all section headings.\n"
            "- Do NOT add any new information or remove existing information.\n"
            "- Ensure the translation is culturally appropriate for a homeschooling parent.\n"
            "- Return ONLY the translated text, with no extra commentary."
        )
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please translate this report into {target_language}:\n\n{report_content}"}
            ]
            
            return await openai_service.get_chat_completion(messages, temperature=0.3)
        except Exception as e:
            logger.error(f"Error translating report: {e}", exc_info=True)
            return report_content  # Fallback to original if translation fails

insight_agent = InsightAgent()

