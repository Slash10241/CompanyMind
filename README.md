# CompanyMind — Industrial Knowledge Intelligence Platform

An AI-powered knowledge platform that ingests heterogeneous business and industrial documents, builds a unified knowledge graph, and makes their collective intelligence queryable through a conversational copilot.

Built for the **Unstop Hackathon — Theme 8: AI for Industrial Knowledge Intelligence**.

---

## Features

- **Document Ingestion Pipeline** — Upload PDFs, TXT, CSV files; extracts entities (equipment tags, personnel, orders, products, regulations, dates) and builds a knowledge graph automatically
- **Expert Knowledge Copilot** — RAG-powered chat with streaming responses, source citations, confidence scores, and direct document links
- **Knowledge Graph Visualiser** — Interactive force-directed graph showing relationships across all ingested documents (10 entity types)
- **Mobile-responsive UI** — Designed for field technicians on phones as well as desktop engineers
- **Hybrid Retrieval** — Vector similarity search (ChromaDB) + knowledge graph traversal for richer, cross-document answers

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI / LLM | Google Gemini 2.5 Flash |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Knowledge Graph | NetworkX |
| PDF Parsing | PyMuPDF |
| Frontend | React 18, Vite, Tailwind CSS |
| Graph Viz | react-force-graph-2d |

---

## Dataset

This project uses the **Company Documents Dataset** from Kaggle (invoices, shipping orders, purchase orders, and inventory reports in PDF format).

**Download:** [https://www.kaggle.com/datasets/navodpeiris/company-documents-dataset](https://www.kaggle.com/datasets/navodpeiris/company-documents-dataset)

After downloading, extract and place the folder at:

```
backend/data/CompanyDocuments/
├── invoices/                    # ~830 PDF invoices
├── shipping_orders/             # ~809 PDF shipping orders
├── purchase_orders/             # ~830 PDF purchase orders
├── inventory_monthly/           # ~23 monthly stock reports
└── inventory_monthly_category/  # ~184 category-level stock reports
```

> The dataset is excluded from this repository via `.gitignore`. You must download it separately.

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Google AI Studio](https://aistudio.google.com/) API key (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/Slash10241/CompanyMind.git
cd CompanyMind
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend && npm install && cd ..
```

### 5. Download and place the dataset

Download from the Kaggle link above and extract to `backend/data/CompanyDocuments/` as shown in the Dataset section.

---

## Running the Platform

### Option A — Quick start script

```bash
chmod +x start.sh
./start.sh
```

This generates synthetic data (first run only), starts the FastAPI backend on `:8000`, and the Vite frontend on `:5173`.

### Option B — Manual start

**Terminal 1 — Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Loading Documents

### Option A — Bulk ingest the Kaggle dataset

```bash
# Ingest 40 files per category (~200 documents, ~5 minutes)
python3 scripts/ingest_company_docs.py

# Quick test with fewer files
python3 scripts/ingest_company_docs.py --limit 5

# Ingest everything (2,676 files — slow)
python3 scripts/ingest_company_docs.py --limit 0
```

### Option B — Generate synthetic industrial documents

```bash
python3 scripts/generate_synthetic_data.py
```

Generates 27 realistic "Sunrise Refinery" documents (work orders, inspection reports, safety procedures, equipment data sheets, incident reports, operating procedures) and saves them to `backend/data/synthetic/`.

### Option C — Upload via UI

Drag and drop any PDF, TXT, or CSV file onto the **Ingest Documents** panel in the sidebar.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ingest` | Upload and ingest documents |
| `POST` | `/api/chat/stream` | Streaming chat (SSE) |
| `POST` | `/api/chat` | Non-streaming chat |
| `GET` | `/api/graph` | Full knowledge graph |
| `GET` | `/api/graph/entity/{name}` | Subgraph for a specific entity |
| `GET` | `/api/documents` | List all ingested documents |
| `GET` | `/api/documents/{id}/download` | Download original file |
| `GET` | `/api/health` | Server health + stats |

Interactive API docs available at **http://localhost:8000/docs**

---

## Project Structure

```
CompanyMind/
├── backend/
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Settings (loaded from .env)
│   ├── ingestion/                   # Document parsing, entity extraction, graph building
│   ├── rag/                         # Vector store, hybrid retriever, Gemini copilot
│   ├── api/                         # REST endpoints
│   ├── models/                      # Pydantic schemas
│   └── data/                        # Runtime data (gitignored)
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── components/              # Chat, KnowledgeGraph, DocumentUpload, etc.
│       └── lib/api.ts               # API client
├── scripts/
│   ├── generate_synthetic_data.py   # Synthetic industrial document generator
│   └── ingest_company_docs.py       # Bulk dataset ingestion script
├── .env.example                     # Environment variable template
└── start.sh                         # One-command startup script
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | **required** |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./backend/data/chroma` |
| `UPLOADS_DIR` | Uploaded files storage | `./backend/data/uploads` |
| `SYNTHETIC_DATA_DIR` | Generated docs path | `./backend/data/synthetic` |
