from __future__ import annotations
from typing import Generator
import google.generativeai as genai
from backend.config import settings
from backend.rag.retriever import retrieve, build_citations
from backend.models.schemas import SourceCitation

_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(
            model_name=settings.chat_model,
            system_instruction=SYSTEM_PROMPT,
        )
    return _model


SYSTEM_PROMPT = """You are an Expert Knowledge Copilot for an industrial and business knowledge base.
You assist engineers, technicians, and analysts by answering questions about equipment, procedures, regulations, operational history, orders, inventory, and procurement.

RULES:
1. Answer ONLY from the provided context documents. Do not use external knowledge.
2. Cite your sources inline as [Document Name, p.N] after each key fact.
3. If the context is insufficient to answer, say "I don't have enough information in the knowledge base to answer this reliably."
4. Be concise and direct — users need actionable answers.
5. For safety-critical questions, always remind the user to verify with the original procedure.
6. When multiple documents agree, state that explicitly — it increases confidence."""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(
            f"[Source {i}: {c['doc_name']}, page {c.get('page_number', 1)}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def stream_answer(query: str, history: list[dict]) -> Generator[str, None, None]:
    """Stream answer tokens from Gemini."""
    chunks, _ = retrieve(query, top_k=settings.top_k_retrieval)
    context = _build_context(chunks)

    gemini_history = []
    for msg in history[-6:]:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    model = _get_model()
    chat = model.start_chat(history=gemini_history)
    user_content = f"Context documents:\n{context}\n\n---\nQuestion: {query}"

    try:
        response = chat.send_message(
            user_content,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            yield "\n\n⚠️ **Rate limit reached.** Please wait a moment and try again."
        else:
            yield f"\n\n❌ **Error:** {err[:200]}"


def answer_with_metadata(query: str, history: list[dict]) -> tuple[str, list[SourceCitation], float]:
    """Non-streaming answer with citations and confidence."""
    chunks, confidence = retrieve(query, top_k=settings.top_k_retrieval)
    context = _build_context(chunks)

    gemini_history = []
    for msg in history[-6:]:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    model = _get_model()
    chat = model.start_chat(history=gemini_history)
    user_content = f"Context documents:\n{context}\n\n---\nQuestion: {query}"

    try:
        response = chat.send_message(
            user_content,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        answer = response.text
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            answer = "⚠️ Rate limit reached. Please wait a moment and try again."
        else:
            answer = f"❌ Error: {err[:200]}"

    citations = build_citations(chunks)
    return answer, citations, confidence
