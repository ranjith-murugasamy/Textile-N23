#!/usr/bin/env bash
# Run the research pipeline end to end: data -> analysis -> results/ (metrics.json, tables, figures) -> manuscript.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
PY=.venv/bin/python
$PY src/fetch_data.py        # verifies data/raw/bbd_table3.csv and writes the coded design
$PY src/run_experiments.py   # writes results/metrics.json and results/tables/*.csv
$PY src/make_figures.py      # writes results/figures/*.png, a .md beside each, and output/explanations.txt
$PY src/build_paper.py       # writes ../manuscript/manuscript.json from metrics.json
$PY src/build_manuscript.py ../manuscript/manuscript.json output/Manuscript_CA-CN-Rotor-Yarn.docx
$PY src/build_cover_letter.py
$PY src/highlight_changes.py output/Manuscript_CA-CN-Rotor-Yarn.docx output/Manuscript_CA-CN-Rotor-Yarn_changes-highlighted.docx
