# CompanyMind — Knowledge Intelligence Platform

An AI-powered platform that ingests heterogeneous business and industrial documents and makes their collective intelligence queryable through a conversational copilot with source citations and confidence scoring.

Built for the **Unstop Hackathon — Theme 8: AI for Industrial Knowledge Intelligence**.

---

## Features

- **2-Step RAG Routing** — Before every query the agent decides whether knowledge-base retrieval is needed. Greetings and general questions get a direct conversational reply; document queries trigger full hybrid retrieval. Each response is labelled **"KB searched"** or **"Direct reply"**.
- **Hybrid RAG Retrieval** — Vector similarity search (ChromaDB) combined with knowledge-graph neighbour expansion (NetworkX) for richer, cross-document answers.
- **Smart Listing Query Detection** — Queries containing `list / all / highest / maximum / cheapest` etc. bypass the default top-8 limit and retrieve all documents of the matched type (up to 50), enabling complete answers like "list all invoices".
- **Streaming AI Chat** — Token-by-token SSE streaming with confidence badge and collapsible source citations on every RAG answer.
- **3-Key Gemini Failover** — Automatically rotates through up to three API keys on 429/quota errors. Streaming rotation only triggers before the first token so partial responses are never corrupted.
- **Universal Document Ingestion** — Upload PDFs, TXT, CSV, or Markdown. Doc type is inferred from the filename (Invoice, Work Order, Inventory Report, Purchase Order, etc.).
- **Entity Extraction** — 10 entity types extracted by Gemini at ingest time: `EQUIPMENT_TAG`, `PERSON`, `DATE`, `REGULATION`, `PARAMETER`, `LOCATION`, `FAILURE_MODE`, `ORDER_ID`, `PRODUCT`, `ORGANISATION`.
- **Mobile-responsive UI** — Desktop sidebar + mobile bottom-nav, built with React 18 + Tailwind CSS.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI / LLM | Google Gemini 2.5 Flash (chat, routing, entity extraction) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, no API cost) |
| Vector Store | ChromaDB (persistent, cosine HNSW index) |
| Knowledge Graph | NetworkX DiGraph (co-occurrence edges) |
| PDF Parsing | PyMuPDF (fitz) |
| Settings | pydantic-settings |
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS (custom navy/gold theme) |

---

## How the 2-Step Chat Works

```
User message
     │
     ▼
Step 1 ── Router (Gemini, temp=0) ──► 0 (no RAG) ──► Direct conversational reply
                                  └─► 1 (RAG)    ──► ChromaDB retrieval
                                                       + Graph expansion
                                                       + Gemini synthesis
                                                       + Citations & confidence
```

**SSE event sequence:**

```
data: {"type": "rag_decision", "needs_rag": 0|1}
data: {"type": "metadata",     "confidence": 0.87|null, "citations": [...]}
data: {"type": "token",        "text": "Hello..."}
...
data: {"type": "done"}
```

---

## Dataset

This project uses the **Company Documents Dataset** from Kaggle.

**Download:** [kaggle.com/datasets/navodpeiris/company-documents-dataset](https://www.kaggle.com/datasets/navodpeiris/company-documents-dataset)

| Category | Files | Content |
|---|---|---|
| Inventory Report | ~207 | Monthly stock snapshots |
| Invoice | ~830 | Customer billing records |
| Shipping Order | ~809 | Freight/delivery orders |
| Purchase Order | ~830 | Supplier procurement docs |

After downloading, extract to `backend/data/CompanyDocuments/`. The dataset is gitignored — download separately.

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- At least one [Google AI Studio](https://aistudio.google.com/) API key (free tier works)

### 1. Clone

```bash
git clone https://github.com/Slash10241/CompanyMind.git
cd CompanyMind
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY_1=your_primary_key
GEMINI_API_KEY_2=your_second_key   # optional — used on quota errors
GEMINI_API_KEY_3=your_third_key    # optional — last fallback
```

### 3. Install backend

```bash
pip install -r backend/requirements.txt
```

### 4. Install frontend

```bash
cd frontend && npm install && cd ..
```

---

## Running

**Terminal 1 — Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend && npm run dev
```

Open **http://localhost:5173**

---

## Loading Documents

### Bulk ingest the Kaggle dataset

```bash
# ~200 documents (40 per category, ~5 min)
python3 scripts/ingest_company_docs.py

# Quick test
python3 scripts/ingest_company_docs.py --limit 5

# Everything (2,676 files)
python3 scripts/ingest_company_docs.py --limit 0
```

### Upload via UI

Drag and drop any PDF, TXT, or CSV onto the **Ingest Documents** panel in the sidebar.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ingest` | Upload and ingest documents |
| `POST` | `/api/chat/stream` | Streaming chat via SSE (2-step routed) |
| `POST` | `/api/chat` | Non-streaming chat |
| `GET` | `/api/graph` | Full knowledge graph `{nodes, edges}` |
| `GET` | `/api/graph/entity/{name}` | Subgraph for a specific entity |
| `POST` | `/api/graph/rebuild` | Re-extract entities from all docs (SSE progress) |
| `GET` | `/api/documents` | List all ingested documents |
| `GET` | `/api/documents/{id}/download` | Download original file |
| `GET` | `/api/health` | Server health + chunk/node/edge counts |

Interactive docs: **http://localhost:8000/docs**

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY_1` | Primary Gemini API key | **required** |
| `GEMINI_API_KEY_2` | Second key (quota fallback) | optional |
| `GEMINI_API_KEY_3` | Third key (last fallback) | optional |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./backend/data/chroma` |
| `UPLOADS_DIR` | Uploaded files storage | `./backend/data/uploads` |
| `SYNTHETIC_DATA_DIR` | Synthetic docs path | `./backend/data/synthetic` |
| `TOP_K_RETRIEVAL` | Default chunks retrieved | `8` |
| `CHUNK_SIZE` | Tokens per chunk | `800` |
| `CHUNK_OVERLAP` | Overlap between chunks | `100` |

---

## Project Structure

```
CompanyMind/
├── backend/
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # pydantic-settings config (3-key support)
│   ├── gemini_keys.py              # Key rotation: call_with_fallback / stream_with_fallback
│   ├── ingestion/
│   │   ├── pdf_parser.py           # PyMuPDF text extraction + chunking
│   │   ├── entity_extractor.py     # Gemini entity extraction (10 types)
│   │   ├── graph_builder.py        # NetworkX co-occurrence graph
│   │   └── pipeline.py             # Orchestrates ingest + rebuild
│   ├── rag/
│   │   ├── vector_store.py         # ChromaDB CRUD + doc-type filter
│   │   ├── retriever.py            # Hybrid retrieval + listing query detection
│   │   └── copilot.py              # Router (needs_rag), direct reply, RAG answer
│   ├── api/
│   │   ├── chat.py                 # 2-step SSE stream endpoint
│   │   ├── ingest.py               # File upload endpoint
│   │   ├── graph.py                # Graph + rebuild endpoints
│   │   └── documents.py            # Document list + download
│   └── models/schemas.py           # Pydantic models
├── frontend/
│   └── src/
│       ├── App.tsx                 # Tab layout (Copilot / Documents)
│       ├── components/
│       │   ├── ChatInterface.tsx   # Streaming chat + RAG/Direct badge
│       │   ├── ConfidenceBadge.tsx # Colour-coded confidence pill
│       │   ├── SourceCitation.tsx  # Collapsible source cards
│       │   ├── DocumentUpload.tsx  # Drag-and-drop uploader
│       │   └── DocumentList.tsx    # Ingested document cards
│       └── lib/api.ts              # API client + SSE stream parser
├── scripts/
│   ├── generate_synthetic_data.py  # Synthetic industrial doc generator
│   └── ingest_company_docs.py      # Bulk Kaggle dataset ingestion
└── .env.example
```
