#!/usr/bin/env bash
# Install backend (Python venv) and frontend (npm) dependencies.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r backend/requirements.txt
[ ! -f requirements.txt ] || .venv/bin/pip install -q -r requirements.txt
(cd frontend && npm install --no-audit --no-fund)
echo "setup complete"
