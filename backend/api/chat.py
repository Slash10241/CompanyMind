import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.models.schemas import ChatRequest
from backend.rag.copilot import needs_rag, stream_direct, stream_answer, answer_with_metadata
from backend.rag.retriever import retrieve, build_citations

router = APIRouter()


async def _event_stream(query: str, history: list[dict]):
    # ── Step 1: decide whether RAG is needed ──────────────────────────────────
    rag_required = needs_rag(query, history)
    yield f"data: {json.dumps({'type': 'rag_decision', 'needs_rag': int(rag_required)})}\n\n"

    if not rag_required:
        # ── Step 2a: direct conversational reply (no retrieval) ───────────────
        yield f"data: {json.dumps({'type': 'metadata', 'confidence': None, 'citations': []})}\n\n"
        for token in stream_direct(query, history):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
    else:
        # ── Step 2b: retrieve → cite → stream RAG answer ──────────────────────
        chunks, confidence = retrieve(query, top_k=8)
        citations = build_citations(chunks)
        yield f"data: {json.dumps({'type': 'metadata', 'confidence': confidence, 'citations': [c.model_dump() for c in citations]})}\n\n"
        for token in stream_answer(query, history, chunks=chunks):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    history = [m.model_dump() for m in request.history]
    return StreamingResponse(
        _event_stream(request.query, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """Non-streaming endpoint for testing."""
    history = [m.model_dump() for m in request.history]
    answer, citations, confidence = answer_with_metadata(request.query, history)
    return {
        "answer": answer,
        "citations": [c.model_dump() for c in citations],
        "confidence": confidence,
    }
