# Execution log (fresh `.venv`, macOS arm64, Python 3.14.3, Node 24.21)

SETUP: PASS
- `scripts/setup.sh`: venv created, pinned requirements installed, `npm install` done; log ends "setup complete" (`results/logs/setup.log`).

PIPELINE: PASS
- `scripts/run_pipeline.sh`: fetch_data (15 runs, sha256 verified) -> run_experiments (metrics.json, 7 CSV tables) -> make_figures (11 charts + metrics_summary) -> build_paper -> build_manuscript (15 figures, 9 tables, 30 references) -> cover letter. About 30 s.

BACKEND_TESTS: PASS
- `.venv/bin/python -m pytest -q tests backend/tests`: 6 passed (design geometry, OLS recovery, desirability, metrics contract, API tests).

FRONTEND_BUILD: PASS
- `npm run build` (Vite): built in under 1 s, `dist/assets/index-*.js` 145 kB.

API_SMOKE: PASS
- uvicorn on :8765; `GET /api/health` -> `{"ok":true,"has_metrics":true}`; `GET /api/metrics` returned the metrics JSON (seed 20231123, n_runs 15); `GET /api/figures` listed the PNGs. Server stopped.

Other checks: humanize_check pass; overlap_check shares 3.15% of 8-grams with the authors' own draft (their methods text and FTIR peak list), 0% with both reference PDFs, 0.1% with the review file.

Follow-up: `src/highlight_changes.py` wrote `output/Manuscript_CA-CN-Rotor-Yarn_changes-highlighted.docx` (yellow = new or rewritten vs the authors' original draft). PIPELINE re-run not repeated; the step was run directly and added to `scripts/run_pipeline.sh`.
