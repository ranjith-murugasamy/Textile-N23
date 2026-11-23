#!/usr/bin/env python3
"""Build the journal manuscript (.docx, two-column journal style) from a JSON spec.

usage: python3 build_manuscript.py manuscript/manuscript.json manuscript/Manuscript.docx
Spec: {"header_left", "header_right", "title", "authors", "affiliations": [], "corresponding",
       "abstract", "keywords", "sections": [{"heading": "1. Introduction", "blocks": [
         {"type": "p", "text": "..."}, {"type": "h2", "text": "..."}, {"type": "bullet", "text": "..."},
         {"type": "equation", "text": "...", "number": 1},
         {"type": "figure", "path": "../results/figures/x.png", "caption": "...", "width_cm": 8.4},
         {"type": "table", "caption": "...", "header": [..], "rows": [[..]], "widths": [..]}]}],
       "back_matter": [{"heading": "Conflicts of Interest", "text": "..."}], "references": ["..."]}
Paths are relative to the spec file. *italic* spans are supported in text.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from docx_builder import Paper  # noqa: E402


def build(spec_path: Path, out: Path) -> dict:
    s = json.loads(spec_path.read_text())
    base = spec_path.parent
    p = Paper(s.get("header_left", ""), s.get("header_right", ""))
    p.title(s["title"], s.get("authors", ""), s.get("affiliations", []), s.get("corresponding", ""))
    p.abstract("Abstract", s["abstract"])
    p.abstract("Keywords", s["keywords"])
    p.start_two_columns()
    for sec in s["sections"]:
        p.h1(sec["heading"])
        for b in sec["blocks"]:
            t = b["type"]
            if t == "p":
                p.para(b["text"])
            elif t == "h2":
                p.h2(b["text"])
            elif t == "bullet":
                p.bullet(b["text"])
            elif t == "equation":
                p.equation(b["text"], b.get("number", 1))
            elif t == "figure":
                fig = (base / b["path"]).resolve()
                if not fig.is_file():
                    raise FileNotFoundError(f"figure missing: {fig}")
                p.figure(fig, b["caption"], b.get("width_cm", 8.4))
            elif t == "table":
                p.table(b["caption"], b["header"], b["rows"], b.get("widths"), b.get("font", 8))
            else:
                raise ValueError(f"unknown block type: {t}")
    for bm in s.get("back_matter", []):
        p.h1(bm["heading"])
        p.para(bm["text"], indent=False)
    p.references(s["references"])
    out.parent.mkdir(parents=True, exist_ok=True)
    p.save(out)
    return {"figures": p.fig, "tables": p.tab, "out": str(out)}


if __name__ == "__main__":
    print(json.dumps(build(Path(sys.argv[1]), Path(sys.argv[2]))))
