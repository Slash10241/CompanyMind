import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.models.schemas import ChatRequest
from backend.rag.copilot import stream_answer, answer_with_metadata
from backend.rag.retriever import retrieve, build_citations

router = APIRouter()


async def _event_stream(query: str, history: list[dict]):
    # First, compute citations and confidence (fast retrieval)
    chunks, confidence = retrieve(query, top_k=8)
    citations = build_citations(chunks)

    # Send metadata event first
    meta_event = {
        "type": "metadata",
        "confidence": confidence,
        "citations": [c.model_dump() for c in citations],
    }
    yield f"data: {json.dumps(meta_event)}\n\n"

    # Stream answer tokens
    for token in stream_answer(query, history):
        event = {"type": "token", "text": token}
        yield f"data: {json.dumps(event)}\n\n"

    # Send done signal
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
