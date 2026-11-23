# Textile N-23: response-surface re-analysis of cigarette-filter / comber-noil rotor yarns

Python pipeline (OLS, ANOVA, bootstrap, desirability) + FastAPI results API + React/Tailwind dashboard. Input: the 15-run Box-Behnken table from the authors' draft (`data/raw/bbd_table3.csv`, rounded values).

## Structure
```
backend/    FastAPI results API (app/main.py) and tests
frontend/   React 18 + Vite + Tailwind CSS dashboard
src/        pipeline: fetch_data.py, run_experiments.py, make_figures.py, models, metrics
data/       dataset (raw/, processed/) and data/README.md with provenance and licence
results/    metrics.json, tables/*.csv, figures/*.png (+ .md explanation beside each figure)
output/     final journal manuscript (.docx) ready to submit
scripts/    setup.sh, run_pipeline.sh, run_app.sh
```

## Run
```bash
scripts/setup.sh          # venv + npm install
scripts/run_pipeline.sh   # produces everything in results/
scripts/run_app.sh        # API http://localhost:8000, dashboard http://localhost:5173
make test                 # backend and pipeline tests
```

## results/metrics.json contract
`{"headline": {"<label>": <number>, ...}, ...}`; the dashboard shows `headline` as cards. Every figure `results/figures/<name>.png` has `<name>.md` with its explanation.

## Expected outputs and runtime
- `results/metrics.json`, `results/tables/*.csv` (audit of printed equations, ANOVA, coefficients, reduced models, optimum vs benchmark), `results/figures/fig_01..11 + metrics_summary` (each with a `.md` explanation).
- `../manuscript/manuscript.json` and `output/Manuscript_CA-CN-Rotor-Yarn.docx`, `output/cover_letter.docx`, all PNG charts and `output/explanations.txt`.
- Runtime: about 30 s for the whole pipeline (4000 bootstrap refits of five models) on a CPU laptop. There is no training stage.
- Hardware used: Apple-silicon Mac, macOS, Python 3.14, Node 24.

## Notes
- The analysis uses rounded values printed in the draft; rerun on the unrounded laboratory records before submission.
- `pip install pypdf` is needed only for `src/overlap_check.py` when a reference is a PDF.
- Not available and not invented: mass balance, contaminant assays, resource use, confirmation run (see `data/README.md`).
