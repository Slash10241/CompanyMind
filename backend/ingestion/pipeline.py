from __future__ import annotations
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone

from backend.config import settings
from backend.ingestion.pdf_parser import parse_document
from backend.ingestion.entity_extractor import extract_entities
from backend.ingestion import graph_builder
from backend.rag.vector_store import add_chunks
from backend.models.schemas import IngestionResult, DocumentMetadata

_doc_registry_file = "./backend/data/documents.json"


def _load_registry() -> dict:
    if Path(_doc_registry_file).exists():
        return json.loads(Path(_doc_registry_file).read_text())
    return {}


def _save_registry(registry: dict):
    Path(_doc_registry_file).parent.mkdir(parents=True, exist_ok=True)
    Path(_doc_registry_file).write_text(json.dumps(registry, default=str))


def _infer_doc_type(filename: str) -> str:
    name = filename.lower()
    # Industrial documents
    if "work_order" in name or "wo_" in name:
        return "Work Order"
    if "inspection" in name or "insp_" in name:
        return "Inspection Report"
    if "safety" in name or "procedure" in name or "sop" in name:
        return "Safety Procedure"
    if "data_sheet" in name or "datasheet" in name or "eds_" in name:
        return "Equipment Data Sheet"
    if "incident" in name or "near_miss" in name or "inc_" in name:
        return "Incident Report"
    if "operating" in name or "ops_" in name:
        return "Operating Procedure"
    # Business/company documents
    if "invoice" in name:
        return "Invoice"
    if "shipping" in name or "order_" in name or name.startswith("order"):
        return "Shipping Order"
    if "purchase" in name:
        return "Purchase Order"
    if "stockreport" in name or "inventory" in name or "stock" in name:
        return "Inventory Report"
    return "General Document"


async def ingest_file(file_path: str, original_name: str) -> IngestionResult:
    """Full ingestion pipeline: parse → extract entities → embed → update graph."""
    doc_id = str(uuid.uuid4())
    doc_type = _infer_doc_type(original_name)

    # Parse document into chunks
    chunks = parse_document(file_path, settings.chunk_size, settings.chunk_overlap)

    # Extract entities and build graph
    all_entities = []
    total_nodes = 0
    total_edges = 0
    for chunk in chunks:
        entities = extract_entities(chunk["text"])
        all_entities.extend(entities)
        n, e = graph_builder.add_entities_from_chunk(entities, doc_id, original_name)
        total_nodes += n
        total_edges += e

    # Store chunks in vector store
    chunk_dicts = [
        {
            "text": c["text"],
            "doc_id": doc_id,
            "doc_name": original_name,
            "doc_type": doc_type,
            "page_number": c["page_number"],
            "entities": json.dumps([e.text for e in all_entities[:20]]),
        }
        for c in chunks
    ]
    add_chunks(chunk_dicts)

    # Persist graph
    graph_builder.save_graph()

    # Save doc metadata
    registry = _load_registry()
    registry[doc_id] = DocumentMetadata(
        id=doc_id,
        name=original_name,
        doc_type=doc_type,
        file_path=file_path,
        upload_time=datetime.now(timezone.utc).isoformat(),
        chunk_count=len(chunks),
        entity_count=len(set(e.text for e in all_entities)),
        page_count=chunks[-1]["page_number"] if chunks else 0,
    ).model_dump()
    _save_registry(registry)

    return IngestionResult(
        doc_id=doc_id,
        doc_name=original_name,
        chunk_count=len(chunks),
        entity_count=len(set(e.text for e in all_entities)),
        graph_nodes_added=total_nodes,
        graph_edges_added=total_edges,
    )


def list_documents() -> list[DocumentMetadata]:
    registry = _load_registry()
    return [DocumentMetadata(**v) for v in registry.values()]


def get_document(doc_id: str) -> DocumentMetadata | None:
    registry = _load_registry()
    if doc_id in registry:
        return DocumentMetadata(**registry[doc_id])
    return None
