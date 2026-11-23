"""Small helpers that lay out a python-docx document in the IJIES two-column house style."""
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor

FONT = "Times New Roman"


def _font(run, size=10, bold=False, italic=False):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size); run.bold = bold; run.italic = italic


def set_columns(section, n, space_cm=0.6):
    cols = section._sectPr.xpath("./w:cols")
    el = cols[0] if cols else OxmlElement("w:cols")
    el.set(qn("w:num"), str(n)); el.set(qn("w:space"), str(int(space_cm * 567)))
    if not cols:
        section._sectPr.append(el)


class Paper:
    def __init__(self, header_left, header_right):
        self.doc = Document()
        s = self.doc.sections[0]
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin = s.right_margin = Cm(1.9); s.top_margin = Cm(2.2); s.bottom_margin = Cm(2.0)
        st = self.doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(10)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        self._header(s, header_left, header_right)
        self.fig = self.tab = 0

    def _header(self, section, left, right):
        h = section.header; p = h.paragraphs[0]; p.text = ""
        r = p.add_run(left); _font(r, 8)
        p.add_run("\n"); r2 = p.add_run(right); _font(r2, 8)
        pf = section.footer.paragraphs[0]; pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = pf.add_run(); _font(run, 8)
        for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tag); run._r.append(f)
            else:
                it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; run._r.append(it)

    # ---- single-column front matter
    def title(self, text, authors, affiliations, corresponding):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _font(p.add_run(text), 17, bold=True); p.paragraph_format.space_after = Pt(8)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _font(p.add_run(authors), 11, bold=True)
        for a in affiliations:
            p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _font(p.add_run(a), 9); p.paragraph_format.space_after = Pt(0)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _font(p.add_run(corresponding), 9); p.paragraph_format.space_after = Pt(8)

    def abstract(self, label, text):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        _font(p.add_run(label + ": "), 9.5, bold=True); _font(p.add_run(text), 9.5)

    def start_two_columns(self):
        sec = self.doc.add_section(WD_SECTION.CONTINUOUS)
        set_columns(sec, 2)

    # ---- body
    def h1(self, text):
        p = self.doc.add_paragraph(); p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        _font(p.add_run(text), 11, bold=True)

    def h2(self, text):
        p = self.doc.add_paragraph(); p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        _font(p.add_run(text), 10, bold=True)

    def para(self, text, indent=True):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(4)
        if indent:
            p.paragraph_format.first_line_indent = Cm(0.5)
        self._rich(p, text, 10)

    def _rich(self, p, text, size):
        """Supports *italic* spans; everything else is plain."""
        parts = text.split("*")
        for i, part in enumerate(parts):
            if part:
                _font(p.add_run(part), size, italic=(i % 2 == 1))

    def bullet(self, text):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.4)
        p.paragraph_format.space_after = Pt(2)
        self._rich(p, "• " + text, 10)

    def equation(self, expr, number):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(3)
        _font(p.add_run(f"{expr}        ({number})"), 10, italic=True)

    def figure(self, path, caption, width_cm=8.4):
        self.fig += 1
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(4)
        p.add_run().add_picture(str(path), width=Cm(width_cm))
        c = self.doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after = Pt(6)
        _font(c.add_run(f"Figure. {self.fig} "), 9, bold=True); self._rich(c, caption, 9)
        return self.fig

    def table(self, caption, header, rows, widths=None, font=8):
        self.tab += 1
        c = self.doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.keep_with_next = True; c.paragraph_format.space_before = Pt(4); c.paragraph_format.space_after = Pt(2)
        _font(c.add_run(f"Table {self.tab}. "), 9, bold=True); self._rich(c, caption, 9)
        t = self.doc.add_table(rows=1, cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.style = "Table Grid"
        for i, h in enumerate(header):
            cell = t.rows[0].cells[i]; cell.text = ""
            r = cell.paragraphs[0].add_run(h); _font(r, font, bold=True)
            tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "E7ECF2"); tcPr.append(sh)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                r = cells[i].paragraphs[0].add_run(str(v)); _font(r, font)
                if i > 0:
                    cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        sp = self.doc.add_paragraph(); sp.paragraph_format.space_after = Pt(4)
        return self.tab

    def references(self, refs):
        self.h1("References")
        for i, r in enumerate(refs, 1):
            p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.9)
            p.paragraph_format.space_after = Pt(2)
            _font(p.add_run(f"[{i}] {r}"), 8.5)

    def save(self, path):
        self.doc.save(str(path))
