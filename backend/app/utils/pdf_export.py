"""PDF export generator using fpdf2 for research reports."""

import io
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from typing import Optional, List, Dict, Any


class ResearchReportPDF(FPDF):
    """Custom PDF generator with professional editorial styling."""

    def __init__(self, title: str):
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 140)
            self.set_x(18)
            clean_hdr = _clean_text_for_pdf(f"AgentVerse Research Report - {self.report_title[:50]}...")
            self.cell(self.epw, 8, clean_hdr, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 160)
        self.set_x(18)
        self.cell(self.epw, 10, f"Page {self.page_no()}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _clean_text_for_pdf(text: str) -> str:
    """Sanitize unsupported unicode characters for standard PDF Helvetica font."""
    if not text:
        return ""
    replacements = {
        "—": " - ",
        "–": " - ",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "\u200b": "",
        "\u202f": " ",
        "©": "(c)",
        "®": "(R)",
        "™": "(TM)",
        "→": "->",
        "←": "<-",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf_report(
    title: str,
    executive_summary: str,
    full_markdown: str,
    sources: Optional[List[Dict[str, Any]]] = None
) -> bytes:
    """Generate high-quality PDF bytes for a completed research report."""
    pdf = ResearchReportPDF(title=title)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)
    epw = pdf.epw

    # Title Block
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 26, 46)
    pdf.set_x(18)
    pdf.multi_cell(epw, 9, _clean_text_for_pdf(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Subtitle / Platform meta
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 80, 140)
    pdf.set_x(18)
    pdf.cell(epw, 6, "AGENTVERSE MULTI-AGENT RESEARCH & INTELLIGENCE SYSTEM", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(160, 150, 200)
    pdf.set_line_width(0.5)
    line_y = pdf.get_y() + 2
    pdf.line(18, line_y, 18 + epw, line_y)
    pdf.ln(6)

    # Executive Summary Callout Box
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(40, 30, 80)
    pdf.set_x(18)
    pdf.cell(epw, 6, "Executive Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    pdf.set_fill_color(245, 245, 252)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 50)
    pdf.set_x(18)
    pdf.multi_cell(epw, 6, _clean_text_for_pdf(executive_summary), fill=True, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Body sections parsing from markdown
    lines = full_markdown.split("\n")
    skip_header = False
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            pdf.ln(2)
            continue

        if line_clean.startswith("# ") or line_clean.startswith("## "):
            header_text = re.sub(r"^#+\s*", "", line_clean)
            if "Executive Summary" in header_text:
                skip_header = True
                continue
            skip_header = False
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 25, 60)
            pdf.set_x(18)
            pdf.multi_cell(epw, 7, _clean_text_for_pdf(header_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_draw_color(200, 200, 220)
            pdf.set_line_width(0.2)
            pdf.line(18, pdf.get_y(), 18 + epw, pdf.get_y())
            pdf.ln(3)
        elif line_clean.startswith("### "):
            subhead = re.sub(r"^###\s*", "", line_clean)
            skip_header = False
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(50, 50, 70)
            pdf.set_x(18)
            pdf.multi_cell(epw, 6, _clean_text_for_pdf(subhead), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
        elif line_clean.startswith("- ") or line_clean.startswith("* "):
            if skip_header:
                continue
            bullet_text = line_clean[2:].strip().replace("**", "")
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(40, 40, 50)
            pdf.set_x(18)
            pdf.multi_cell(epw, 5.5, _clean_text_for_pdf(f"*  {bullet_text}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            if skip_header:
                continue
            p_text = line_clean.replace("**", "")
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(40, 40, 50)
            pdf.set_x(18)
            pdf.multi_cell(epw, 5.5, _clean_text_for_pdf(p_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Sources / References section if provided
    if sources:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 25, 60)
        pdf.set_x(18)
        pdf.cell(epw, 7, "Verified References & Citations", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_line_width(0.2)
        pdf.line(18, pdf.get_y(), 18 + epw, pdf.get_y())
        pdf.ln(4)

        for s in sources:
            num = s.get("citation_number", "")
            num_str = f"[{num}] " if num else "* "
            title_s = s.get("title", "Untitled Source")
            domain_s = s.get("domain", "")
            url_s = s.get("url", "")
            date_s = f" ({s.get('publication_date')})" if s.get("publication_date") else ""

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 30, 40)
            pdf.set_x(18)
            line_str = _clean_text_for_pdf(f"{num_str}{title_s}{date_s}")
            pdf.multi_cell(epw, 5, line_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 80, 160)
            pdf.set_x(18)
            ref_meta = _clean_text_for_pdf(f"    Domain: {domain_s} | Link: {url_s}")
            pdf.multi_cell(epw, 4.5, ref_meta, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

    return bytes(pdf.output())
