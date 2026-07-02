import re
from backend.rag import vector_store
from backend.ingestion import graph_builder
from backend.models.schemas import SourceCitation

# Known entity prefixes to detect equipment tags and regulation codes in queries
_EQUIP_PATTERN = re.compile(r'\b([A-Z]-\d{3}[A-Z]?)\b', re.IGNORECASE)
_REG_PATTERN = re.compile(r'\b(OISD|PESO|ISO|API|BIS|Factory Act|OHSAS)\b', re.IGNORECASE)


def _extract_query_entities(query: str) -> list[str]:
    entities = []
    entities += _EQUIP_PATTERN.findall(query)
    entities += _REG_PATTERN.findall(query)
    return list(set(e.upper() for e in entities))


def retrieve(query: str, top_k: int = 8) -> tuple[list[dict], float]:
    """
    Hybrid retrieval: vector similarity + knowledge graph neighbor expansion.
    Returns (ranked_chunks, confidence_score).
    """
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
