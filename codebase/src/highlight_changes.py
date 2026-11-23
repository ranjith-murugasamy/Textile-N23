"""Write a copy of the manuscript in which text that is new or rewritten relative to the authors' original draft
(inputs/current_paper/Paper.docx) is highlighted yellow. Sentences whose word 6-grams are mostly present in the draft
are left plain. Tables 1-3 carry the draft's own data, so only their captions are tested; other table cells are new."""
import copy
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX

import config as C

DRAFT = C.ROOT.parent.parent / "inputs" / "current_paper" / "Paper.docx"
N = 6
CARRIED_TABLES = 3


def words(t: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", t.lower())


def draft_text(path: Path) -> str:
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        parts += [c.text for r in t.rows for c in r.cells]
    return " ".join(parts)


def grams(w: list[str]) -> set:
    return {tuple(w[i:i + N]) for i in range(len(w) - N + 1)}


def is_new(sentence: str, dg: set, dwords: str) -> bool:
    w = words(sentence)
    if len(w) < N:
        return " ".join(w) not in dwords if w else False
    g = grams(w)
    return len(g & dg) / len(g) < 0.6


def mark_paragraph(p, flags_fn) -> int:
    """Highlight character ranges returned by flags_fn(text) -> list of (start, end); split runs as needed."""
    runs = list(p.runs)
    text = "".join(r.text for r in runs)
    spans = flags_fn(text)
    if not spans:
        return 0
    hl = [False] * len(text)
    for a, b in spans:
        for i in range(a, b):
            hl[i] = True
    pos = 0
    for r in runs:
        n = len(r.text)
        seg = hl[pos:pos + n]
        if n and any(seg):
            if all(seg):
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW
            else:  # split the run at highlight boundaries
                pieces, start = [], 0
                for i in range(1, n + 1):
                    if i == n or seg[i] != seg[start]:
                        pieces.append((start, i, seg[start]))
                        start = i
                base = r.text
                r.text = base[pieces[0][0]:pieces[0][1]]
                if pieces[0][2]:
                    r.font.highlight_color = WD_COLOR_INDEX.YELLOW
                anchor = r._r
                for a, b, h in pieces[1:]:
                    new = copy.deepcopy(r._r)
                    anchor.addnext(new)
                    anchor = new
                    from docx.text.run import Run
                    nr = Run(new, p)
                    nr.text = base[a:b]
                    nr.font.highlight_color = WD_COLOR_INDEX.YELLOW if h else None
        pos += n
    return sum(hl)


def main(src: Path, out: Path) -> None:
    dtxt = draft_text(DRAFT)
    dwords = " ".join(words(dtxt))
    dg = grams(words(dtxt))
    doc = Document(src)
    in_refs = False
    stats = {"new_chars": 0, "plain_chars": 0}

    def sentence_spans(text: str):
        spans = []
        for m in re.finditer(r".+?(?:[.!?](?=\s|$)|$)", text, re.S):
            s = m.group(0)
            if s.strip() and is_new(s, dg, dwords):
                spans.append((m.start(), m.end()))
        return spans

    dset = set(dwords.split())

    def ref_spans(text: str):
        nums = [n for n in re.findall(r"\d{3,}", text) if not n.startswith(("19", "20"))]
        hit = sum(n in dset for n in nums)
        return [] if nums and hit / len(nums) >= 0.5 else [(0, len(text))]

    for p in doc.paragraphs:
        t = p.text
        if t.strip().startswith("References"):
            in_refs = True
        if not t.strip():
            continue
        n = mark_paragraph(p, ref_spans if in_refs and re.match(r"\[\d+\]", t) else sentence_spans)
        stats["new_chars"] += n
        stats["plain_chars"] += len(t) - n
    for ti, tbl in enumerate(doc.tables):
        if ti < CARRIED_TABLES:
            continue
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text.strip():
                        stats["new_chars"] += mark_paragraph(p, lambda t: [(0, len(t))])
    # captions are ordinary paragraphs, handled above. Legend as the first paragraph.
    first = doc.paragraphs[0]
    leg = copy.deepcopy(first._p)
    first._p.addprevious(leg)
    from docx.text.paragraph import Paragraph
    lp = Paragraph(leg, first._parent)
    for r in lp.runs[1:]:
        r._r.getparent().remove(r._r)
    lp.runs[0].text = "Yellow highlight marks text, tables and references that are new or rewritten relative to the authors' original draft; unhighlighted text is carried over unchanged (sentence-level 6-gram match, threshold 60%)."
    lp.runs[0].font.highlight_color = WD_COLOR_INDEX.YELLOW
    lp.runs[0].font.bold = False
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    tot = stats["new_chars"] + stats["plain_chars"]
    print(f"highlighted {100 * stats['new_chars'] / tot:.1f}% of body characters -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
