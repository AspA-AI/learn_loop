import logging
from openai import AsyncOpenAI, OpenAIError, APIStatusError, RateLimitError
from core.config import settings
from typing import List, Dict, Any, Optional
from services.opik_service import opik_service

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set. OpenAI features will not work.")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"

    async def get_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        try:
            with opik_service.span(
                name="openai.chat.completions.create",
                span_type="llm",
                input={
                    "model": self.model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": response_format,
                    "messages": messages,
                },
                model=self.model,
                provider="openai",
            ) as span:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format
                )
                content = response.choices[0].message.content

                # Attach high-value LLM metrics for Opik dashboards:
                # - usage tokens (prompt/completion/total)
                # - finish_reason
                # - output text (bounded)
                # Opik supports cost tracking; we include usage so it can compute/visualize it.
                usage = getattr(response, "usage", None)
                prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
                completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
                total_tokens = getattr(usage, "total_tokens", None) if usage else None
                finish_reason = None
                try:
                    finish_reason = response.choices[0].finish_reason
                except Exception:
                    finish_reason = None

                # Keep output preview bounded to avoid huge payloads in tracing.
                out_preview = content
                if isinstance(out_preview, str) and len(out_preview) > 1200:
                    out_preview = out_preview[:1200] + "…"

                try:
                    if span is not None:
                        span.update(
                            output={"content": out_preview},
                            metadata={
                                "openai_usage": {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": total_tokens,
                                },
                                "finish_reason": finish_reason,
                            },
                        )
                except Exception:
                    # Tracing must never break the app
                    pass

                return content
        except RateLimitError as e:
            logger.error(f"OpenAI Rate Limit exceeded: {e}")
            raise e
        except APIStatusError as e:
            logger.error(f"OpenAI API returned an error: {e.status_code} - {e.message}")
            raise e
        except OpenAIError as e:
            logger.error(f"OpenAI general error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}", exc_info=True)
            raise e

    async def transcribe_audio(self, audio_file: Any, language: Optional[str] = None) -> str:
        try:
            # Map full language name to ISO code for Whisper
            lang_map = {
                'English': 'en',
                'German': 'de',
                'French': 'fr',
                'Portuguese': 'pt',
                'Spanish': 'es',
                'Italian': 'it',
                'Turkish': 'tr'
            }
            lang_code = lang_map.get(language) if language else None

            with opik_service.span(
                name="openai.audio.transcriptions.create",
                span_type="llm",
                input={
                    "model": "whisper-1",
                    "language": lang_code,
                    "filename": audio_file[0] if isinstance(audio_file, tuple) and len(audio_file) > 0 else None,
                },
                model="whisper-1",
                provider="openai",
            ) as span:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=lang_code
                )
                text = response.text
                out_preview = text
                if isinstance(out_preview, str) and len(out_preview) > 1200:
                    out_preview = out_preview[:1200] + "…"
                try:
                    if span is not None:
                        span.update(output={"text": out_preview})
                except Exception:
                    pass
                return text
        except Exception as e:
            logger.error(f"Error during audio transcription: {e}", exc_info=True)
            raise e

    async def text_to_speech(
        self,
        text: str,
        language: Optional[str] = None,
        voice: str = "alloy",
    ) -> bytes:
        """
        Text-to-speech for child-facing playback.
        Uses OpenAI TTS and returns MP3 bytes.
        """
        try:
            # Keep instructions simple; provide language to improve pronunciation.
            instructions = None
            if language:
                instructions = f"Speak naturally in {language}."

            with opik_service.span(
                name="openai.audio.speech.create",
                span_type="llm",
                input={
                    "model": "gpt-4o-mini-tts",
                    "voice": voice,
                    "language": language,
                    "text_len": len(text or ""),
                },
                model="gpt-4o-mini-tts",
                provider="openai",
            ) as span:
                audio = await self.client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice=voice,
                    input=text,
                    response_format="mp3",
                    instructions=instructions,
                )
                # OpenAI SDK returns HttpxBinaryResponseContent (not raw bytes).
                # Extract bytes safely.
                if hasattr(audio, "read") and callable(getattr(audio, "read")):
                    data = audio.read()
                elif hasattr(audio, "content"):
                    data = audio.content  # type: ignore[attr-defined]
                else:
                    # Fallback for unexpected SDK shapes
                    data = bytes(audio)  # type: ignore[arg-type]
                try:
                    if span is not None:
                        span.update(output={"bytes": len(data)})
                except Exception:
                    pass
                return data
        except Exception as e:
            logger.error(f"Error during text-to-speech: {e}", exc_info=True)
            raise e

openai_service = OpenAIService()

