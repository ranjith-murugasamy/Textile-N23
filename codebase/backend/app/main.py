"""Results API. Serves what the pipeline wrote to results/: metrics.json, tables/*.csv, figures/*.png + explanations."""
import csv
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
app = FastAPI(title="Results API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"ok": True, "has_metrics": (RESULTS / "metrics.json").exists()}


@app.get("/api/metrics")
def metrics():
    f = RESULTS / "metrics.json"
    if not f.exists():
        raise HTTPException(404, "results/metrics.json not found. Run scripts/run_pipeline.sh first.")
    return json.loads(f.read_text())


@app.get("/api/figures")
def figures():
    out = []
    for png in sorted((RESULTS / "figures").glob("*.png")):
        exp = png.with_suffix(".md")
        out.append({"name": png.name, "url": f"/api/figures/{png.name}", "explanation": exp.read_text() if exp.exists() else ""})
    return out


@app.get("/api/figures/{name}")
def figure(name: str):
    f = (RESULTS / "figures" / Path(name).name)
    if f.suffix != ".png" or not f.is_file():
        raise HTTPException(404, "figure not found")
    return FileResponse(f)


@app.get("/api/tables")
def tables():
    out = {}
    for f in sorted((RESULTS / "tables").glob("*.csv")):
        with f.open(newline="") as fh:
            out[f.stem] = list(csv.reader(fh))
    return out
