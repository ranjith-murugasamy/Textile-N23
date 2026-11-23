#!/usr/bin/env python3
"""Local n-gram overlap between the manuscript body and source texts. Expect headings and metric names only.

usage: python3 overlap_check.py manuscript.docx source1.pdf source2.docx ...
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from humanize_check import body, read_text  # noqa: E402


def pdf_text(p: Path) -> str:
    from pypdf import PdfReader
    return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)


def load(p: Path) -> str:
    return pdf_text(p) if p.suffix.lower() == ".pdf" else read_text(p)


def grams(words, n):
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def check(manuscript: Path, sources: list[Path]) -> list[dict]:
    ms = re.findall(r"[a-z0-9]+", body(load(manuscript)).lower())
    out = []
    for s in sources:
        src = re.findall(r"[a-z0-9]+", load(s).lower())
        row = {"source": s.name}
        for n in (8, 12):
            a = grams(ms, n)
            row[f"shared_{n}grams"] = len(a & grams(src, n))
            row[f"share_{n}_pct"] = round(100 * row[f"shared_{n}grams"] / max(len(a), 1), 2)
        out.append(row)
    return out


if __name__ == "__main__":
    res = check(Path(sys.argv[1]), [Path(x) for x in sys.argv[2:]])
    for r in res:
        print(r)
    sys.exit(1 if any(r["share_12_pct"] > 1.0 for r in res) else 0)
