"""
Bulk-ingest the Kaggle Company Documents dataset into the knowledge platform.
Samples a configurable number of files per category to keep API usage reasonable.

Usage:
  python3 scripts/ingest_company_docs.py              # default: 40 per category
  python3 scripts/ingest_company_docs.py --limit 10   # quick smoke-test
  python3 scripts/ingest_company_docs.py --limit 0    # ingest ALL (slow)
"""
from __future__ import annotations
import sys
import os
import argparse
import asyncio
import random
from pathlib import Path
from dotenv import load_dotenv

# Project root on path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

# Set telemetry off before any chromadb import
import os as _os
_os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from backend.ingestion.pipeline import ingest_file

DATASET_DIR = ROOT / "backend" / "data" / "CompanyDocuments"

CATEGORIES = {
    "invoices":                   "Invoice",
    "shipping_orders":            "Shipping Order",
    "purchase_orders":            "Purchase Order",
    "inventory_monthly":          "Inventory Report",
    "inventory_monthly_category": "Inventory Report",
}


async def ingest_category(category: str, files: list[Path], label: str) -> int:
    ok = 0
    for i, f in enumerate(files, 1):
        try:
            result = await ingest_file(str(f), f.name)
            ok += 1
            print(f"  [{i}/{len(files)}] {f.name} → {result.chunk_count} chunks, {result.entity_count} entities")
        except Exception as e:
            print(f"  [{i}/{len(files)}] {f.name} ERROR: {e}")
    return ok


async def main(limit: int):
    print(f"=== Company Documents Bulk Ingestion ===")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Limit per category: {'ALL' if limit == 0 else limit}\n")

    total_ok = 0
    total_files = 0

    for subdir, label in CATEGORIES.items():
        cat_dir = DATASET_DIR / subdir
        if not cat_dir.exists():
            print(f"[SKIP] {subdir} — directory not found")
            continue

        all_files = sorted(cat_dir.glob("*.pdf"))
        if not all_files:
            print(f"[SKIP] {subdir} — no PDF files found")
            continue

        # Sample or take all
        if limit > 0 and len(all_files) > limit:
            files = random.sample(all_files, limit)
        else:
            files = all_files

        print(f">>> {label} ({subdir}): ingesting {len(files)}/{len(all_files)} files")
        ok = await ingest_category(subdir, files, label)
        total_ok += ok
        total_files += len(files)
        print(f"    Done: {ok}/{len(files)} succeeded\n")

    print(f"=== Ingestion complete: {total_ok}/{total_files} files processed ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=40,
                        help="Max files per category (0 = all, default 40)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for sampling")
    args = parser.parse_args()
    random.seed(args.seed)
    asyncio.run(main(args.limit))
