#!/bin/bash
# Sunrise Refinery Knowledge Intelligence Platform — Quick Start

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Sunrise Refinery KIP — Starting ==="

# Check API key
if grep -q "your_gemini_api_key_here" "$ROOT/.env"; then
  echo "ERROR: Set GEMINI_API_KEY in .env before starting"
  exit 1
fi

# Generate synthetic data if not already done
if [ ! -f "$ROOT/backend/data/synthetic/manifest.json" ]; then
  echo ">>> Generating synthetic Sunrise Refinery documents..."
  cd "$ROOT" && python3 scripts/generate_synthetic_data.py
fi

# Start backend
echo ">>> Starting FastAPI backend on :8000..."
cd "$ROOT" && uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to come up
sleep 3

# Start frontend
echo ">>> Starting Vite frontend on :5173..."
cd "$ROOT/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== Platform running ==="
echo "  Frontend:  http://localhost:5173"
echo "  API docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

cleanup() {
  echo "Stopping servers..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup INT TERM
wait
