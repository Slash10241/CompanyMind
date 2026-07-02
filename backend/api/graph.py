from fastapi import APIRouter
from backend.ingestion.graph_builder import get_graph_data, get_subgraph, get_node_count, get_edge_count
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
