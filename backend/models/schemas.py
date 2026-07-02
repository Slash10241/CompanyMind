from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Entity(BaseModel):
    text: str
    type: str  # EQUIPMENT_TAG, PERSON, DATE, REGULATION, PARAMETER, LOCATION, FAILURE_MODE
    context_snippet: str = ""


class DocumentMetadata(BaseModel):
    id: str
    name: str
    doc_type: str
    file_path: str
    upload_time: str
    chunk_count: int = 0
    entity_count: int = 0
    page_count: int = 0


class IngestionResult(BaseModel):
    doc_id: str
    doc_name: str
    chunk_count: int
    entity_count: int
    graph_nodes_added: int
    graph_edges_added: int


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    history: list[ChatMessage] = Field(default_factory=list)


class SourceCitation(BaseModel):
    doc_id: str
    doc_name: str
    page_number: int
    snippet: str
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[SourceCitation]
    confidence: float


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    doc_count: int = 0
    color: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0
    relation: str = "co-occurs"


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
