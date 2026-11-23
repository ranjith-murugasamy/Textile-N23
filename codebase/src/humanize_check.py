#!/usr/bin/env python3
"""Prose-quality scan for a manuscript (.docx, .md or .txt). Flags stock phrases and monotone rhythm.

This checks writing quality (specific, varied, natural academic prose). It is not an AI-detector evasion tool;
authors must still review the text and follow the target journal's AI-assistance disclosure policy.

usage: python3 humanize_check.py manuscript.docx [--json out.json]   exit code 1 if the text needs work
"""
import json
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

STOCK = ["delve", "tapestry", "in today's rapidly evolving", "rapidly evolving", "it is important to note", "it is worth noting",
         "plays a crucial role", "plays a pivotal role", "pivotal", "paradigm shift", "game-changer", "cutting-edge", "state-of-the-art landscape",
         "in the realm of", "navigate the complexities", "unlock the potential", "harness the power", "seamless", "holistic", "robust and scalable",
         "testament to", "shed light on", "a myriad of", "underscores the importance", "in conclusion, this paper", "this comprehensive",
         "meticulously", "leverag", "ever-evolving", "intricate interplay", "foster", "elevate", "revolutioni"]
CONNECTORS = ["furthermore", "moreover", "additionally", "consequently", "thus", "therefore", "hence"]


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        out = subprocess.run(["pandoc", str(path), "-t", "plain", "--wrap=none"], capture_output=True, text=True)
        if out.returncode == 0:
            return out.stdout
        from docx import Document
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    return path.read_text(errors="ignore")


def body(text: str) -> str:
    return re.split(r"\n\s*(?:References|REFERENCES)\s*\n", text)[0]


def analyse(text: str) -> dict:
    t = body(text)
    words = re.findall(r"[A-Za-z']+", t)
    n = max(len(words), 1)
    low = t.lower()
    sents = [s for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", t)) if len(s.split()) >= 4]
    lens = [len(s.split()) for s in sents] or [0]
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    starters = Counter(" ".join(s.split()[:2]).lower() for s in sents)
    top_starter, top_count = (starters.most_common(1) or [("", 0)])[0]
    stock = {p: low.count(p) for p in STOCK if low.count(p)}
    conn = sum(low.count(c) for c in CONNECTORS)
    passive = len(re.findall(r"\b(?:is|are|was|were|been|being)\s+\w+ed\b", low))
    first_person = len(re.findall(r"\b(?:we|our|us)\b", low))
    per_k = lambda x: round(1000 * x / n, 2)
    issues = []
    if sum(stock.values()) > 2:
        issues.append(f"{sum(stock.values())} stock phrases (limit 2): {', '.join(stock)}")
    if cv < 0.40:
        issues.append(f"sentence lengths too uniform (variation {cv:.2f} < 0.40): mix short and long sentences")
    if mean > 28:
        issues.append(f"average sentence length {mean:.0f} words is heavy (aim 18-26)")
    if per_k(conn) > 9:
        issues.append(f"connector density {per_k(conn)}/1000 words (limit 9): cut 'furthermore/moreover/additionally'")
    if sents and top_count / len(sents) > 0.12:
        issues.append(f"{top_count} sentences start with '{top_starter}' ({100 * top_count / len(sents):.0f}%): vary openings")
    if per_k(passive) > 14:
        issues.append(f"passive voice {per_k(passive)}/1000 words: prefer active constructions with 'we'")
    return {"words": n, "sentences": len(sents), "mean_sentence_words": round(mean, 1), "sentence_length_variation": round(cv, 2),
            "stock_phrases": stock, "connectors_per_1000": per_k(conn), "passive_per_1000": per_k(passive),
            "first_person_per_1000": per_k(first_person), "top_starter": [top_starter, top_count], "issues": issues, "pass": not issues}


if __name__ == "__main__":
    res = analyse(read_text(Path(sys.argv[1])))
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["pass"] else 1)
