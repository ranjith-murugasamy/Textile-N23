#!/usr/bin/env python3
"""Verify a final-output folder against the deliverable contract and write readiness_report.md.

usage: python3 readiness_check.py <final-output dir> [--min-figures 5] [--min-pages 8] [--min-tables 3]
Exit code 0 only if every CRITICAL check passes (the deliverable may then be called submission-ready).
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from humanize_check import analyse, read_text  # noqa: E402

REQUIRED_SECTIONS = ["abstract", "introduction", "method", "result", "conclusion", "reference"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--min-figures", type=int, default=5)
    ap.add_argument("--min-tables", type=int, default=3)
    ap.add_argument("--min-pages", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    cb = out / "codebase"
    checks = []                                           # (critical, name, ok, detail)

    def chk(critical, name, ok, detail=""):
        checks.append((critical, name, bool(ok), detail))

    # ---- codebase structure and executability
    for rel in ["backend/app/main.py", "backend/requirements.txt", "frontend/package.json", "frontend/tailwind.config.js", "frontend/src/App.jsx",
                "src", "data/README.md", "results", "scripts/setup.sh", "scripts/run_pipeline.sh", "scripts/run_app.sh", "README.md"]:
        chk(True, f"codebase/{rel}", (cb / rel).exists())
    rd = (cb / "README.md").read_text() if (cb / "README.md").exists() else ""
    chk(True, "README.md has no template placeholders", "<Project title>" not in rd and "<project title>" not in rd.lower())
    pkg = (cb / "frontend/package.json")
    if pkg.exists():
        deps = json.loads(pkg.read_text())
        both = {**deps.get("dependencies", {}), **deps.get("devDependencies", {})}
        chk(True, "frontend uses react and tailwindcss", "react" in both and "tailwindcss" in both)
    log = cb / "EXECUTION_LOG.md"
    log_txt = log.read_text() if log.exists() else ""
    for step in ["SETUP", "PIPELINE", "BACKEND_TESTS", "FRONTEND_BUILD", "API_SMOKE"]:
        chk(True, f"executed and passed: {step}", re.search(rf"^{step}:\s*PASS", log_txt, re.M))
    # ---- results
    figs = sorted((cb / "results/figures").glob("*.png")) if (cb / "results/figures").exists() else []
    chk(True, f"results/figures has >= {a.min_figures} PNG charts", len(figs) >= a.min_figures, f"{len(figs)} found")
    missing = [f.name for f in figs if not f.with_suffix(".md").exists() or len(f.with_suffix(".md").read_text().split()) < 25]
    chk(True, "every figure has an explanation (.md, >= 25 words)", not missing, ", ".join(missing[:5]))
    m = cb / "results/metrics.json"
    try:
        headline = json.loads(m.read_text()).get("headline") if m.exists() else None
    except json.JSONDecodeError:
        headline = None
    chk(True, "results/metrics.json has a non-empty 'headline'", headline)
    tabs = list((cb / "results/tables").glob("*.csv")) if (cb / "results/tables").exists() else []
    chk(False, "results/tables has CSV tables", tabs, f"{len(tabs)} found")
    ds = list((cb / "data").rglob("*")) if (cb / "data").exists() else []
    chk(True, "data/ has content beyond README (or data/README.md documents a fetch script)", len([f for f in ds if f.name != "README.md" and f.is_file()]) > 0
        or "fetch_data.py" in (cb / "data/README.md").read_text() if (cb / "data/README.md").exists() else False)
    # ---- output folder: charts as PNG plus explanations.txt naming each file
    odir0 = cb / "output"
    opngs = sorted(odir0.glob("*.png")) if odir0.is_dir() else []
    chk(True, f"codebase/output/ has >= {a.min_figures} chart PNGs", len(opngs) >= a.min_figures, f"{len(opngs)} found")
    chk(True, "codebase/output/ has a metrics PNG", any("metric" in f.name.lower() for f in opngs))
    ex = odir0 / "explanations.txt"
    ex_txt = ex.read_text() if ex.exists() else ""
    chk(True, "codebase/output/explanations.txt exists", ex.exists())
    unnamed = [f.name for f in opngs if f.name not in ex_txt]
    chk(True, "explanations.txt names every PNG in output/", not unnamed, ", ".join(unnamed[:5]))
    short = []
    for chunk in re.split(r"\n(?=File: )", ex_txt)[1:]:
        if len(chunk.split()) < 30:
            short.append(chunk.splitlines()[0])
    chk(True, "every explanations.txt entry has a real explanation (>= 25 words)", not short, ", ".join(short[:4]))
    # ---- manuscript
    odir = cb / "output"
    chk(True, "codebase/output/ folder exists", odir.is_dir())
    docs = sorted(odir.glob("*.docx")) if odir.is_dir() else []
    chk(True, "final manuscript .docx is saved in codebase/output/", [d for d in docs if "cover" not in d.name.lower()],
        ", ".join(d.name for d in docs) or "no .docx found (the legacy manuscript/ folder is not accepted)")
    docs = [d for d in docs if "cover" not in d.name.lower()]
    if docs:
        d = docs[0]
        try:
            z = zipfile.ZipFile(d)
            imgs = [n for n in z.namelist() if n.startswith("word/media/")]
            xml = z.read("word/document.xml").decode("utf8", errors="ignore")
            tbls = xml.count("<w:tbl>")
            text = read_text(d)
            words = len(re.findall(r"\w+", text))
            low = text.lower()
            chk(True, f"manuscript embeds >= {a.min_figures} figures", len(imgs) >= a.min_figures, f"{len(imgs)} images")
            chk(True, f"manuscript has >= {a.min_tables} tables", tbls >= a.min_tables, f"{tbls} tables")
            missing_sec = [s for s in REQUIRED_SECTIONS if s not in low]
            chk(True, "manuscript has the standard sections", not missing_sec, ", ".join(missing_sec))
            pages = words / 900 + len(imgs) * 0.28 + tbls * 0.2 + 0.6
            chk(True, f"estimated length >= {a.min_pages} pages", pages >= a.min_pages, f"about {pages:.1f} pages ({words} words); confirm in Word")
            refs = len(set(re.findall(r"^\s*\[(\d{1,3})\]", text, re.M)))
            chk(True, "manuscript has >= 20 numbered references", refs >= 20, f"{refs} found")
            hz = analyse(text)
            chk(True, "humanization scan passes", hz["pass"], "; ".join(hz["issues"]) or "ok")
            ph = sorted(set(re.findall(r"\[[A-Za-z][^\]]{2,60}\]", text)) - set(re.findall(r"\[\d+\]", text)))
            ph = [p for p in ph if not re.fullmatch(r"\[\d+(?:[,–-]\s*\d+)*\]", p)]
            ph = [p for p in ph if not re.search(r"[∈=()^_\\<>+*/]", p)]          # bracketed math such as [R_u(r) ∈ T_u] is not a placeholder
            chk(False, "placeholders to fill before submission", not ph, "; ".join(ph[:8]))
        except zipfile.BadZipFile:
            chk(True, "manuscript .docx opens", False, "not a valid docx")
    # ---- review status
    rs = out / "review_status.json"
    try:
        items = json.loads(rs.read_text()) if rs.exists() else None
    except json.JSONDecodeError:
        items = None
    chk(True, "review_status.json is a valid list", isinstance(items, list))

    crit_fail = [c for c in checks if c[0] and not c[2]]
    ready = not crit_fail
    lines = ["# Readiness report", "", f"**Status: {'SUBMISSION-READY (pending author review and a commercial similarity check)' if ready else 'NOT SUBMISSION-READY'}**", "",
             "| Check | Critical | Result | Detail |", "|---|---|---|---|"]
    for crit, name, ok, detail in checks:
        lines.append(f"| {name} | {'yes' if crit else 'no'} | {'PASS' if ok else 'FAIL'} | {detail} |")
    if crit_fail:
        lines += ["", "## Blocking items", *[f"- {c[1]} {('(' + c[3] + ')') if c[3] else ''}" for c in crit_fail]]
    (out / "readiness_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
