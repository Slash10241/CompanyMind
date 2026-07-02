"""
Ingest all generated synthetic Sunrise Refinery documents into the knowledge platform.
Run this after generate_synthetic_data.py.

Usage:
  python3 scripts/ingest_synthetic_data.py
"""
from __future__ import annotations
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import os
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from backend.ingestion.pipeline import ingest_file

SYNTHETIC_DIR = ROOT / "backend" / "data" / "synthetic"


async def main():
    pdfs = sorted(SYNTHETIC_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {SYNTHETIC_DIR}")
        print("Run `python3 scripts/generate_synthetic_data.py` first.")
        return

    print(f"Ingesting {len(pdfs)} synthetic documents from {SYNTHETIC_DIR}\n")
    for i, pdf in enumerate(pdfs, 1):
        try:
            result = await ingest_file(str(pdf), pdf.name)
            print(f"[{i}/{len(pdfs)}] {pdf.name}")
            print(f"         {result.chunk_count} chunks · {result.entity_count} entities · +{result.graph_nodes_added} nodes")
        except Exception as e:
            print(f"[{i}/{len(pdfs)}] {pdf.name} — ERROR: {e}")

    print("\nDone! Open http://localhost:5173 to query the knowledge base.")


if __name__ == "__main__":
    asyncio.run(main())
