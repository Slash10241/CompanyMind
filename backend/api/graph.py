import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.ingestion.graph_builder import get_graph_data, get_subgraph, get_node_count, get_edge_count
from backend.ingestion.pipeline import rebuild_graph_from_registry
from backend.models.schemas import GraphData

router = APIRouter()


@router.get("/graph", response_model=GraphData)
async def full_graph():
    return get_graph_data()


@router.get("/graph/entity/{entity_name}", response_model=GraphData)
async def entity_subgraph(entity_name: str):
    return get_subgraph(entity_name)


@router.get("/graph/stats")
async def graph_stats():
    return {
        "node_count": get_node_count(),
        "edge_count": get_edge_count(),
    }


@router.post("/graph/rebuild")
async def rebuild_graph():
    """Stream progress while re-extracting entities from all registered docs."""
    def event_stream():
        for progress in rebuild_graph_from_registry():
            yield f"data: {json.dumps(progress)}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
