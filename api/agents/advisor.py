import json
import logging
from typing import Any, Dict, List, Optional

from services.openai_service import openai_service

logger = logging.getLogger(__name__)


class AdvisorAgent:
    """
    Parent-facing advisor that discusses a selected child's learning progress,
    aligns expectations, and collects preferences / constraints to steer future sessions.
    """

    async def respond(
        self,
        parent_name: Optional[str],
        child_name: str,
        child_age: Optional[int],
        child_learning_profile: Optional[Dict[str, Any]],
        guidance_notes: List[str],
        child_overall_progress_context: Optional[str],
        focus_session_context: Optional[str],
        chat_history: List[Dict[str, str]],
        parent_message: str,
        language: str = "English",
    ) -> str:
        system = (
            "You are the Parent Advisor Agent inside a homeschooling learning app.\n"
            "You speak to a parent (adult). Your job:\n"
            "- Help them understand the child's learning progress and patterns.\n"
            "- Align expectations and suggest actionable, realistic next steps.\n"
            "- Collect preferences for future child sessions (tone, pacing, tricky areas, goals, focus topics).\n"
            "- Ask clarifying questions when needed.\n"
            "Hard rules:\n"
            "- Do NOT ask the parent to re-provide the child's learning profile (it's already available).\n"
            "- Do NOT claim you have data that isn't provided.\n"
            "- If the parent asks about a specific session, stick to the provided session transcript/evaluation.\n"
            "- Keep responses concise and practical.\n"
            f"Respond in {language}.\n"
        )

        child_block = f"Child: {child_name}"
        if child_age is not None:
            child_block += f" (age {child_age})"

        profile_block = ""
        if child_learning_profile:
            profile_block = json.dumps(child_learning_profile, ensure_ascii=False)

        notes_block = "\n".join([f"- {n}" for n in guidance_notes]) if guidance_notes else "(none yet)"

        overall_block = child_overall_progress_context or "(not available)"

        focus_block = focus_session_context or "(no specific session selected)"

        user = (
            f"Parent name: {parent_name or 'Parent'}\n"
            f"{child_block}\n\n"
            f"Child learning profile (do not ask parent to restate): {profile_block or '(not provided)'}\n\n"
            f"Existing parent guidance notes (newest first):\n{notes_block}\n\n"
            f"Overall child progress summary (use this for trends; do not invent missing data):\n{overall_block}\n\n"
            f"Selected session context (if any):\n{focus_block}\n\n"
            f"Parent message:\n{parent_message}\n"
        )

        messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
        # include a small amount of history for conversational continuity
        if chat_history:
            messages.extend(chat_history[-12:])
        messages.append({"role": "user", "content": user})

        return await openai_service.get_chat_completion(messages=messages, temperature=0.4, max_tokens=600)


class ParentGuidanceSummarizerAgent:
    """
    Extracts actionable parent guidance notes from a parent<->advisor chat turn.
    Returns a list of short 'notes' strings. Caller stores them append-only.
    """

    async def extract_notes(
        self,
        child_name: str,
        recent_chat: List[Dict[str, str]],
        language: str = "English",
    ) -> List[str]:
        system = (
            "You are a summarizer that extracts actionable parent guidance notes.\n"
            "Output MUST be valid JSON with this shape:\n"
            '{ "notes": ["...","..."] }\n'
            "Rules:\n"
            "- Notes must be short, actionable, and specific.\n"
            "- Capture: goals, preferred tone, pacing, tricky areas, focus topics, constraints.\n"
            "- Do NOT include private or sensitive data.\n"
            "- If there is nothing actionable, return {\"notes\":[]}.\n"
            f"Write notes in {language}.\n"
        )

        convo = "\n".join([f'{m["role"].upper()}: {m["content"]}' for m in recent_chat[-16:]])
        user = (
            f"Child: {child_name}\n\n"
            f"Recent chat:\n{convo}\n\n"
            "Extract actionable notes."
        )

        text = await openai_service.get_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        try:
            obj = json.loads(text or "{}")
            notes = obj.get("notes", [])
            if not isinstance(notes, list):
                return []
            cleaned: List[str] = []
            for n in notes:
                if isinstance(n, str):
                    s = n.strip()
                    if s:
                        cleaned.append(s)
            # de-dupe while preserving order
            seen = set()
            uniq = []
            for n in cleaned:
                key = n.lower()
                if key in seen:
                    continue
                seen.add(key)
                uniq.append(n)
            return uniq[:5]
        except Exception as e:
            logger.warning(f"Failed to parse guidance notes JSON: {e}. Raw: {text}")
            return []


advisor_agent = AdvisorAgent()
parent_guidance_summarizer = ParentGuidanceSummarizerAgent()


