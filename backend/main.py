from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.api import ingest, chat, graph, documents
from backend.ingestion import graph_builder
from backend.rag.vector_store import get_total_chunks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load persisted knowledge graph on startup
    graph_builder.load_graph()
    yield


app = FastAPI(
    title="Industrial Knowledge Intelligence API",
    description="AI-powered knowledge platform for Sunrise Refinery",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(graph.router, prefix="/api", tags=["Knowledge Graph"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "graph_nodes": graph_builder.get_node_count(),
        "graph_edges": graph_builder.get_edge_count(),
        "total_chunks": get_total_chunks(),
    }
