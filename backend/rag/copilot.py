from __future__ import annotations
from typing import Generator
import google.generativeai as genai
from backend.config import settings
from backend.gemini_keys import call_with_fallback, stream_with_fallback
from backend.rag.retriever import retrieve, build_citations
from backend.models.schemas import SourceCitation

# ── System prompts ─────────────────────────────────────────────────────────────

_ROUTER_PROMPT = """You are a query router for a document knowledge base.
Decide whether the user's message requires searching the knowledge base to answer.

Output ONLY the single digit 0 or 1. No explanation, no punctuation — just the digit.

Output 1 (RAG needed) when the message asks about:
- Specific documents, invoices, orders, reports, inventory, or records
- Equipment, procedures, regulations, or technical details
- Prices, quantities, dates, names, or any factual data from documents
- Anything that requires looking up stored information

Output 0 (no RAG needed) when the message is:
- A greeting or farewell (hi, hello, thanks, bye)
- Small talk or a general question answerable from common knowledge
- A clarification about the assistant's capabilities
- A follow-up that is already fully answered by the previous assistant turn"""

_RAG_SYSTEM_PROMPT = """You are an Expert Knowledge Copilot for an industrial and business knowledge base.
You assist engineers, technicians, and analysts by answering questions about equipment, procedures, regulations, operational history, orders, inventory, and procurement.

RULES:
1. Answer ONLY from the provided context documents. Do not use external knowledge.
2. Cite your sources inline as [Document Name, p.N] after each key fact.
3. If the context is insufficient to answer, say "I don't have enough information in the knowledge base to answer this reliably."
4. Be concise and direct — users need actionable answers.
5. For safety-critical questions, always remind the user to verify with the original procedure.
6. When multiple documents agree, state that explicitly — it increases confidence."""

_DIRECT_SYSTEM_PROMPT = """You are CompanyMind's friendly assistant — a knowledgeable copilot for industrial and business document management.
Answer conversationally and helpfully. Do not invent specific data, document contents, or record values.
If the user seems to be asking about stored documents or records, let them know they can ask about specific topics and you will search the knowledge base."""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(
            f"[Source {i}: {c['doc_name']}, page {c.get('page_number', 1)}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def _gemini_history(history: list[dict]) -> list[dict]:
    return [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]}
        for m in history[-6:]
    ]


# ── Step 1: RAG router ─────────────────────────────────────────────────────────

def needs_rag(query: str, history: list[dict]) -> bool:
    """Return True if the query requires knowledge-base retrieval."""
    gemini_history = _gemini_history(history)

    def fn(model: genai.GenerativeModel) -> str:
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            query,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=4,
            ),
        )
        return response.text.strip()

    try:
        result = call_with_fallback(settings.chat_model, fn, _ROUTER_PROMPT)
        return result.startswith("1")
    except Exception:
        return True  # safe default: always try RAG on error


# ── Step 2a: Direct (no-RAG) streaming ────────────────────────────────────────

def stream_direct(query: str, history: list[dict]) -> Generator[str, None, None]:
    """Stream a conversational reply without touching the knowledge base."""
    gemini_history = _gemini_history(history)

    def fn_stream(model: genai.GenerativeModel):
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            query,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=512,
            ),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    try:
        yield from stream_with_fallback(settings.chat_model, fn_stream, _DIRECT_SYSTEM_PROMPT)
    except Exception as e:
        yield f"\n\n❌ **Error:** {str(e)[:200]}"


# ── Step 2b: RAG streaming ─────────────────────────────────────────────────────

def stream_answer(query: str, history: list[dict], chunks: list[dict] | None = None) -> Generator[str, None, None]:
    """Stream answer tokens grounded in retrieved knowledge-base chunks."""
    if chunks is None:
        chunks, _ = retrieve(query, top_k=settings.top_k_retrieval)
    context = _build_context(chunks)
    gemini_history = _gemini_history(history)
    user_content = f"Context documents:\n{context}\n\n---\nQuestion: {query}"

    def fn_stream(model: genai.GenerativeModel):
        chat = model.start_chat(history=gemini_history)
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

    try:
        yield from stream_with_fallback(settings.chat_model, fn_stream, _RAG_SYSTEM_PROMPT)
    except Exception as e:
        yield f"\n\n❌ **Error:** {str(e)[:200]}"


# ── Non-streaming (testing) ────────────────────────────────────────────────────

def answer_with_metadata(query: str, history: list[dict]) -> tuple[str, list[SourceCitation], float]:
    """Non-streaming RAG answer with citations and confidence."""
    chunks, confidence = retrieve(query, top_k=settings.top_k_retrieval)
    context = _build_context(chunks)
    gemini_history = _gemini_history(history)
    user_content = f"Context documents:\n{context}\n\n---\nQuestion: {query}"

    def fn(model: genai.GenerativeModel) -> str:
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(
            user_content,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        return response.text

    try:
        answer = call_with_fallback(settings.chat_model, fn, _RAG_SYSTEM_PROMPT)
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            answer = "⚠️ Rate limit reached on all API keys. Please try again later."
        else:
            answer = f"❌ Error: {err[:200]}"

    citations = build_citations(chunks)
    return answer, citations, confidence
