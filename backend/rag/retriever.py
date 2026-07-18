import re
from backend.rag import vector_store
from backend.ingestion import graph_builder
from backend.models.schemas import SourceCitation

# Known entity prefixes to detect equipment tags and regulation codes in queries
_EQUIP_PATTERN = re.compile(r'\b([A-Z]-\d{3}[A-Z]?)\b', re.IGNORECASE)
_REG_PATTERN = re.compile(r'\b(OISD|PESO|ISO|API|BIS|Factory Act|OHSAS)\b', re.IGNORECASE)

# Listing / aggregation query detection
_LISTING_TRIGGER = re.compile(
    r'\b(list|all|every|each|enumerate|show|summarize|how many|what are'
    r'|highest|lowest|most|least|maximum|minimum|max|min'
    r'|expensive|cheapest|largest|smallest|biggest'
    r'|total|average|count|top|worst|best)\b', re.I
)
_DOC_TYPE_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r'invoice', re.I),                       'Invoice'),
    (re.compile(r'work.?order', re.I),                   'Work Order'),
    (re.compile(r'inspection', re.I),                    'Inspection Report'),
    (re.compile(r'safety|sop\b', re.I),                  'Safety Procedure'),
    (re.compile(r'equipment.?data|data.?sheet', re.I),   'Equipment Data Sheet'),
    (re.compile(r'incident|near.?miss', re.I),           'Incident Report'),
    (re.compile(r'operating.?proc', re.I),               'Operating Procedure'),
    (re.compile(r'purchase.?order', re.I),               'Purchase Order'),
    (re.compile(r'shipping|shipment', re.I),             'Shipping Order'),
    (re.compile(r'stock.?report|inventory', re.I),       'Inventory Report'),
]


def _detect_list_doc_type(query: str) -> str | None:
    """Return the target doc_type if this is a 'list all X' style query, else None."""
    if not _LISTING_TRIGGER.search(query):
        return None
    for pattern, doc_type in _DOC_TYPE_MAP:
        if pattern.search(query):
            return doc_type
    return None


def _extract_query_entities(query: str) -> list[str]:
    entities = []
    entities += _EQUIP_PATTERN.findall(query)
    entities += _REG_PATTERN.findall(query)
    return list(set(e.upper() for e in entities))


def retrieve(query: str, top_k: int = 8) -> tuple[list[dict], float]:
    """
    Hybrid retrieval: vector similarity + knowledge graph neighbor expansion.
    For 'list all X' queries, uses a doc_type filter to return one chunk per document.
    Returns (ranked_chunks, confidence_score).
    """
    # --- Listing query: fetch all docs of the target type ---
    list_doc_type = _detect_list_doc_type(query)
    if list_doc_type:
        all_chunks = vector_store.get_by_doc_type(list_doc_type, limit=300)
        # Keep one chunk per document (prefer page 1 as it usually has summary/totals)
        best: dict[str, dict] = {}
        for c in all_chunks:
            doc_id = c["doc_id"]
            if doc_id not in best or c["page_number"] < best[doc_id]["page_number"]:
                best[doc_id] = c
        merged = list(best.values())[:50]  # cap context at 50 docs
        return merged, _compute_confidence(merged)

    # --- Normal hybrid retrieval ---
    # 1. Vector search
    vector_results = vector_store.query(query, n_results=top_k)

    # 2. Graph expansion: find related chunks from neighboring entities
    query_entities = _extract_query_entities(query)
    expanded_doc_ids = set()
    for entity_text in query_entities:
        neighbors = graph_builder.get_neighbors(entity_text)
        for nid in neighbors:
            # nid format is "TYPE::TEXT" — extract the node's source docs via graph
            node_data = graph_builder._graph.nodes.get(nid, {})
            expanded_doc_ids.update(node_data.get("docs", set()))

    # 3. Fetch chunks from expanded doc IDs (graph-sourced)
    graph_chunks = []
    seen_doc_ids_from_vector = {c["doc_id"] for c in vector_results}
    for doc_id in expanded_doc_ids - seen_doc_ids_from_vector:
        doc_chunks = vector_store.get_chunks_by_doc_id(doc_id)
        # Score these lower than direct vector hits
        for c in doc_chunks[:2]:  # take top 2 per expanded doc
            c["score"] = 0.4
            graph_chunks.append(c)

    # 4. Merge and dedupe by (doc_id, page_number)
    seen = set()
    merged = []
    for chunk in vector_results + graph_chunks:
        key = (chunk["doc_id"], chunk.get("page_number", 1))
        if key not in seen:
            seen.add(key)
            merged.append(chunk)

    # 5. Sort by score descending, take top_k
    merged.sort(key=lambda x: x["score"], reverse=True)
    merged = merged[:top_k]

    # 6. Confidence score
    confidence = _compute_confidence(merged)

    return merged, confidence


def _compute_confidence(chunks: list[dict]) -> float:
    if not chunks:
        return 0.0
    avg_score = sum(c["score"] for c in chunks) / len(chunks)
    source_diversity = len({c["doc_id"] for c in chunks})
    # Boost if multiple independent sources agree
    if source_diversity >= 3:
        confidence = min(1.0, avg_score * 1.25)
    elif source_diversity == 2:
        confidence = min(1.0, avg_score * 1.1)
    else:
        confidence = avg_score
    return round(confidence, 3)


def build_citations(chunks: list[dict]) -> list[SourceCitation]:
    seen = set()
    citations = []
    for c in chunks:
        key = (c["doc_id"], c.get("page_number", 1))
        if key in seen:
            continue
        seen.add(key)
        snippet = c["text"][:200].replace("\n", " ") + "..."
        citations.append(SourceCitation(
            doc_id=c["doc_id"],
            doc_name=c["doc_name"],
            page_number=int(c.get("page_number", 1)),
            snippet=snippet,
            relevance_score=round(c["score"], 3),
        ))
    return citations[:6]
