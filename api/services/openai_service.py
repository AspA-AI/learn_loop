import logging
from openai import AsyncOpenAI, OpenAIError, APIStatusError, RateLimitError
from core.config import settings
from typing import List, Dict, Any, Optional

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            return response.choices[0].message.content
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

    async def transcribe_audio(self, audio_file: Any) -> str:
        try:
            # transcription = await self.client.audio.transcriptions.create(
            #     model="whisper-1", 
            #     file=audio_file
            # )
            # return transcription.text
            
            # Since audio_file might be a SpooledTemporaryFile from FastAPI UploadFile,
            # we need to make sure we pass it correctly.
            # For now, let's assume it's already in a format Whisper likes or we convert it.
            
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.text
        except Exception as e:
            logger.error(f"Error during audio transcription: {e}", exc_info=True)
            raise e

openai_service = OpenAIService()

