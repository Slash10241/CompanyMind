import json
import networkx as nx
from pathlib import Path
from backend.models.schemas import Entity, GraphNode, GraphEdge, GraphData

# Global in-memory graph (persisted to JSON on disk)
_graph: nx.DiGraph = nx.DiGraph()
_graph_file: str = "./backend/data/knowledge_graph.json"

NODE_COLORS = {
    "EQUIPMENT_TAG": "#3B82F6",   # blue
    "PERSON": "#10B981",           # green
    "DATE": "#F59E0B",             # amber
    "REGULATION": "#EF4444",       # red
    "PARAMETER": "#8B5CF6",        # purple
    "LOCATION": "#F97316",         # orange
    "FAILURE_MODE": "#EC4899",     # pink
    "ORDER_ID": "#06B6D4",         # cyan
    "PRODUCT": "#84CC16",          # lime
    "ORGANISATION": "#A78BFA",     # violet
}


def _node_id(entity: Entity) -> str:
    return f"{entity.type}::{entity.text.strip().upper()}"


def add_entities_from_chunk(entities: list[Entity], doc_id: str, doc_name: str) -> tuple[int, int]:
    """Add entities and co-occurrence edges from a single chunk. Returns (nodes_added, edges_added)."""
    nodes_added = 0
    edges_added = 0
    chunk_node_ids = []

    for entity in entities:
        nid = _node_id(entity)
        if nid not in _graph:
            _graph.add_node(nid, label=entity.text, type=entity.type,
                            color=NODE_COLORS.get(entity.type, "#6B7280"),
                            docs=set(), doc_count=0)
            nodes_added += 1
        _graph.nodes[nid]["docs"].add(doc_id)
        _graph.nodes[nid]["doc_count"] = len(_graph.nodes[nid]["docs"])
        chunk_node_ids.append(nid)

    # Add co-occurrence edges between all entities in the same chunk
    for i in range(len(chunk_node_ids)):
        for j in range(i + 1, len(chunk_node_ids)):
            src, tgt = chunk_node_ids[i], chunk_node_ids[j]
            if _graph.has_edge(src, tgt):
                _graph[src][tgt]["weight"] = _graph[src][tgt].get("weight", 1) + 1
            else:
                _graph.add_edge(src, tgt, weight=1, relation="co-occurs", doc_id=doc_id)
                edges_added += 1

    return nodes_added, edges_added


def get_neighbors(entity_text: str, entity_type: str = None) -> list[str]:
    """Return node IDs of neighbors for a given entity text (fuzzy match on label)."""
    results = []
    query = entity_text.strip().upper()
    for nid, data in _graph.nodes(data=True):
        if query in data.get("label", "").upper():
            if entity_type is None or data.get("type") == entity_type:
                results.extend(list(_graph.neighbors(nid)))
                results.extend(list(_graph.predecessors(nid)))
    return list(set(results))


def get_graph_data() -> GraphData:
    nodes = []
    for nid, data in _graph.nodes(data=True):
        nodes.append(GraphNode(
            id=nid,
            label=data.get("label", nid),
            type=data.get("type", "UNKNOWN"),
            doc_count=data.get("doc_count", 0),
            color=data.get("color", "#6B7280"),
        ))
    edges = []
    for src, tgt, data in _graph.edges(data=True):
        edges.append(GraphEdge(
            source=src,
            target=tgt,
            weight=float(data.get("weight", 1)),
            relation=data.get("relation", "co-occurs"),
        ))
    return GraphData(nodes=nodes, edges=edges)


def get_subgraph(entity_name: str) -> GraphData:
    """Return a subgraph centered on a specific entity."""
    query = entity_name.strip().upper()
    center_nodes = [
        nid for nid, data in _graph.nodes(data=True)
        if query in data.get("label", "").upper()
    ]
    if not center_nodes:
        return GraphData(nodes=[], edges=[])

    neighbor_nodes = set(center_nodes)
    for nid in center_nodes:
        neighbor_nodes.update(_graph.neighbors(nid))
        neighbor_nodes.update(_graph.predecessors(nid))

    sub = _graph.subgraph(neighbor_nodes)
    nodes = [
        GraphNode(
            id=nid,
            label=data.get("label", nid),
            type=data.get("type", "UNKNOWN"),
            doc_count=data.get("doc_count", 0),
            color=data.get("color", "#6B7280"),
        )
        for nid, data in sub.nodes(data=True)
    ]
    edges = [
        GraphEdge(source=s, target=t, weight=float(d.get("weight", 1)), relation=d.get("relation", "co-occurs"))
        for s, t, d in sub.edges(data=True)
    ]
    return GraphData(nodes=nodes, edges=edges)


def save_graph():
    """Persist graph to JSON (sets are not JSON-serializable, convert to lists)."""
    data = nx.node_link_data(_graph)
    for node in data["nodes"]:
        if isinstance(node.get("docs"), set):
            node["docs"] = list(node["docs"])
    Path(_graph_file).parent.mkdir(parents=True, exist_ok=True)
    Path(_graph_file).write_text(json.dumps(data))


def load_graph():
    """Load graph from JSON on startup."""
    global _graph
    if Path(_graph_file).exists():
        data = json.loads(Path(_graph_file).read_text())
        for node in data["nodes"]:
            if isinstance(node.get("docs"), list):
                node["docs"] = set(node["docs"])
        _graph = nx.node_link_graph(data)
    else:
        _graph = nx.DiGraph()


def get_node_count() -> int:
    return _graph.number_of_nodes()


def get_edge_count() -> int:
    return _graph.number_of_edges()
