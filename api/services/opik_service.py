import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional

from core.config import settings

logger = logging.getLogger(__name__)

# Track current thread_id so child sessions / parent chats group nicely in Opik UI
_current_thread_id: ContextVar[Optional[str]] = ContextVar("opik_thread_id", default=None)


def set_opik_thread_id(thread_id: Optional[str]) -> None:
    _current_thread_id.set(thread_id)


def get_opik_thread_id() -> Optional[str]:
    return _current_thread_id.get()


class OpikService:
    """
    Thin wrapper around Opik (Comet) that is safe-by-default:
    - If Opik isn't installed OR not configured, all methods become no-ops.
    - If configured, exposes helpers to create request-level traces and nested spans.
    Docs: https://www.comet.com/docs/opik/
    """

    def __init__(self) -> None:
        self._enabled = bool(settings.OPIK_ENABLED) and bool(settings.OPIK_API_KEY)
        self._configured = False
        self._opik = None

        if not self._enabled:
            return

        try:
            import opik  # type: ignore

            self._opik = opik
        except Exception as e:
            logger.warning(f"Opik is not available; tracing disabled. Error: {e}")
            self._enabled = False

    def configure_once(self) -> None:
        if not self._enabled or self._configured or not self._opik:
            return
        try:
            # Opik SDK config (api_key/url/workspace). Project name is passed per trace/span.
            self._opik.configure(
                api_key=settings.OPIK_API_KEY,
                url=settings.OPIK_URL,
            )
            self._configured = True
        except Exception as e:
            logger.warning(f"Failed to configure Opik; tracing disabled. Error: {e}")
            self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def trace(
        self,
        *,
        name: str,
        input: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        thread_id: Optional[str] = None,
    ):
        """
        Context manager that starts an Opik trace.
        We use `thread_id` to group multi-turn conversations.
        """
        if not self._enabled or not self._opik:
            from contextlib import nullcontext

            return nullcontext()

        self.configure_once()
        tid = thread_id or get_opik_thread_id()
        return self._opik.start_as_current_trace(
            name=name,
            input=input,
            metadata=metadata,
            tags=tags,
            project_name=settings.OPIK_PROJECT,
            thread_id=tid,
        )

    def span(
        self,
        *,
        name: str,
        span_type: str = "general",
        input: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        Context manager for a nested span (LLM call, tool call, guardrail, etc.).
        """
        if not self._enabled or not self._opik:
            from contextlib import nullcontext

            return nullcontext()

        self.configure_once()
        return self._opik.start_as_current_span(
            name=name,
            type=span_type,
            input=input,
            metadata=metadata,
            tags=tags,
            project_name=settings.OPIK_PROJECT,
            model=model,
            provider=provider,
        )


opik_service = OpikService()


