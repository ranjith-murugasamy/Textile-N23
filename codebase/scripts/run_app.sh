#!/usr/bin/env bash
# Start the API on :8000 and the dashboard on :5173.
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/uvicorn backend.app.main:app --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd frontend && npm run dev
