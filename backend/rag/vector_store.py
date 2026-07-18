from __future__ import annotations
import os
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
import chromadb
from chromadb.utils import embedding_functions
from backend.config import settings

_client: chromadb.PersistentClient | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        _collection = _client.get_or_create_collection(
            name="industrial_docs",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(chunks: list[dict]):
    """Add text chunks with metadata to the vector store."""
    collection = _get_collection()
    ids = [f"{c['doc_id']}_{i}" for i, c in enumerate(chunks)]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "doc_id": c["doc_id"],
            "doc_name": c["doc_name"],
            "doc_type": c["doc_type"],
            "page_number": int(c.get("page_number", 1)),
            "entities": c.get("entities", ""),
        }
        for c in chunks
    ]
    # ChromaDB batches internally, but chunk large lists to avoid timeout
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i:i + batch_size],
            documents=texts[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )


def query(text: str, n_results: int = 8) -> list[dict]:
    """Return top-n chunks with distance scores."""
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_texts=[text],
        n_results=min(n_results, count),
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        similarity = max(0.0, 1.0 - dist)
        chunks.append({
            "text": doc,
            "doc_id": meta.get("doc_id", ""),
            "doc_name": meta.get("doc_name", ""),
            "doc_type": meta.get("doc_type", ""),
            "page_number": int(meta.get("page_number", 1)),
            "score": round(similarity, 4),
        })
    return chunks


def get_chunks_by_doc_id(doc_id: str) -> list[dict]:
    collection = _get_collection()
    results = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    chunks = []
    for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
        chunks.append({"text": doc, **meta})
    return chunks


def get_by_doc_type(doc_type: str, limit: int = 200) -> list[dict]:
    """Return chunks filtered by exact doc_type value."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    results = collection.get(
        where={"doc_type": doc_type},
        limit=limit,
        include=["documents", "metadatas"],
    )
    chunks = []
    for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
        chunks.append({
            "text": doc,
            "doc_id": meta.get("doc_id", ""),
            "doc_name": meta.get("doc_name", ""),
            "doc_type": meta.get("doc_type", ""),
            "page_number": int(meta.get("page_number", 1)),
            "score": 0.75,
        })
    return chunks


def get_total_chunks() -> int:
    return _get_collection().count()
