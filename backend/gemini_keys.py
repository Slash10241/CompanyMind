from __future__ import annotations
from typing import Callable, Generator, TypeVar
import google.generativeai as genai
from backend.config import settings

T = TypeVar("T")


def _is_quota(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower()


def _make_model(key: str, model_name: str, system_instruction: str | None = None) -> genai.GenerativeModel:
    genai.configure(api_key=key)
    kwargs: dict = {"model_name": model_name}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction
    return genai.GenerativeModel(**kwargs)


def call_with_fallback(
    model_name: str,
    fn: Callable[[genai.GenerativeModel], T],
    system_instruction: str | None = None,
) -> T:
    """Call fn(model) → result, trying each API key in order on quota errors."""
    keys = settings.gemini_api_keys
    last_exc: Exception = RuntimeError("No API keys configured")
    for i, key in enumerate(keys):
        model = _make_model(key, model_name, system_instruction)
        try:
            return fn(model)
        except Exception as e:
            last_exc = e
            if _is_quota(e) and i < len(keys) - 1:
                print(f"[gemini_keys] Key {i+1} quota exceeded, trying key {i+2}…")
                continue
            raise
    raise last_exc


def stream_with_fallback(
    model_name: str,
    fn_stream: Callable[[genai.GenerativeModel], Generator[str, None, None]],
    system_instruction: str | None = None,
) -> Generator[str, None, None]:
    """
    Stream text chunks from fn_stream(model), rotating keys on quota errors.
    Only retries with the next key if no chunks have been yielded yet.
    """
    keys = settings.gemini_api_keys
    for i, key in enumerate(keys):
        model = _make_model(key, model_name, system_instruction)
        chunks_yielded = 0
        try:
            for chunk in fn_stream(model):
                chunks_yielded += 1
                yield chunk
            return  # stream completed successfully
        except Exception as e:
            if _is_quota(e) and chunks_yielded == 0 and i < len(keys) - 1:
                print(f"[gemini_keys] Key {i+1} quota exceeded, trying key {i+2}…")
                continue
            if _is_quota(e):
                yield "\n\n⚠️ **Rate limit reached on all API keys.** Please try again later."
                return
            raise
    yield "\n\n⚠️ **Rate limit reached on all API keys.** Please try again later."
