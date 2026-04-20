"""
Generates QUETOR_PROJECT_REPORT.pdf from QUETOR_PROJECT_REPORT.md
Run: python3 generate_pdf.py
"""

import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Colour palette ──────────────────────────────────────────────────────────
IITK_BLUE   = colors.HexColor("#003b6f")   # IITK dark blue
ACCENT_BLUE = colors.HexColor("#0d6efd")   # highlight blue
LIGHT_BG    = colors.HexColor("#f0f4f8")   # table header / code block bg
MID_GREY    = colors.HexColor("#6c757d")   # secondary text
RULE_GREY   = colors.HexColor("#dee2e6")   # horizontal rules
WHITE       = colors.white
BLACK       = colors.HexColor("#212529")
CODE_BG     = colors.HexColor("#f8f9fa")
CODE_BORDER = colors.HexColor("#e9ecef")
H2_BG       = colors.HexColor("#e8f0fe")   # soft blue for H2 banners

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm

# ── Styles ───────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["title"] = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        textColor=IITK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=ACCENT_BLUE,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["meta"] = ParagraphStyle(
        "meta",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MID_GREY,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    styles["meta_bold"] = ParagraphStyle(
        "meta_bold",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=BLACK,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    styles["toc_title"] = ParagraphStyle(
        "toc_title",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=IITK_BLUE,
        spaceAfter=8,
    )
    styles["toc_entry"] = ParagraphStyle(
        "toc_entry",
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=BLACK,
        leftIndent=12,
    )
    styles["h1"] = ParagraphStyle(
        "h1",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=24,
        textColor=WHITE,
        backColor=IITK_BLUE,
        spaceBefore=18,
        spaceAfter=10,
        leftIndent=-MARGIN + 0.3*cm,
        rightIndent=-MARGIN + 0.3*cm,
        borderPad=8,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=20,
        textColor=IITK_BLUE,
        backColor=H2_BG,
        spaceBefore=14,
        spaceAfter=6,
        borderPad=5,
        leftIndent=-4,
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=IITK_BLUE,
        spaceBefore=10,
        spaceAfter=4,
        borderPadding=(0, 0, 2, 0),
    )
    styles["h4"] = ParagraphStyle(
        "h4",
        fontName="Helvetica-BoldOblique",
        fontSize=10,
        leading=14,
        textColor=MID_GREY,
        spaceBefore=8,
        spaceAfter=3,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9.5,
        leading=15,
        textColor=BLACK,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=BLACK,
        leftIndent=16,
        bulletIndent=4,
        spaceBefore=1,
        spaceAfter=1,
    )
    styles["bullet2"] = ParagraphStyle(
        "bullet2",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=MID_GREY,
        leftIndent=32,
        bulletIndent=18,
        spaceBefore=1,
        spaceAfter=1,
    )
    styles["code"] = ParagraphStyle(
        "code",
        fontName="Courier",
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#c0392b"),
        backColor=CODE_BG,
    )
    styles["code_block"] = ParagraphStyle(
        "code_block",
        fontName="Courier",
        fontSize=7.8,
        leading=11.5,
        textColor=BLACK,
        backColor=CODE_BG,
        leftIndent=10,
    )
    styles["th"] = ParagraphStyle(
        "th",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
    styles["td"] = ParagraphStyle(
        "td",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=BLACK,
    )
    styles["td_code"] = ParagraphStyle(
        "td_code",
        fontName="Courier",
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#c0392b"),
    )
    styles["footer"] = ParagraphStyle(
        "footer",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=MID_GREY,
        alignment=TA_CENTER,
    )
    return styles


# ── Page template with header/footer ────────────────────────────────────────
def make_page_decorator(doc_title="Quetor — Project Report"):
    def decorator(canvas, doc):
        canvas.saveState()
        w, h = A4
        # Top rule
        canvas.setStrokeColor(IITK_BLUE)
        canvas.setLineWidth(2)
        canvas.line(MARGIN, h - 1.2*cm, w - MARGIN, h - 1.2*cm)
        # Header text
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(IITK_BLUE)
        canvas.drawString(MARGIN, h - 1.0*cm, doc_title)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GREY)
        canvas.drawRightString(w - MARGIN, h - 1.0*cm, "IIT Kanpur — UGP")
        # Bottom rule
        canvas.setStrokeColor(RULE_GREY)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 1.4*cm, w - MARGIN, 1.4*cm)
        # Page number
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GREY)
        canvas.drawCentredString(w / 2, 0.8*cm, f"Page {doc.page}")
        canvas.restoreState()
    return decorator


# ── Inline code formatter ────────────────────────────────────────────────────
def fmt_inline(text, td=False):
    """Escape XML and render `backtick` spans as red Courier."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def repl(m):
        inner = m.group(1)
        return f'<font name="Courier" color="#c0392b">{inner}</font>'
    text = re.sub(r"`([^`]+)`", repl, text)
    # bold **...**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # italic *...*
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


# ── Markdown parser → ReportLab flowables ────────────────────────────────────
def parse_markdown(md_text, styles):
    lines = md_text.splitlines()
    story = []
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            in_table = False
            return
        # Filter out separator rows (---|---)
        rows = [r for r in table_rows if not re.match(r"^\s*\|?[\s\-|:]+\|?\s*$", r[0] if r else "")]
        if not rows:
            in_table = False
            table_rows = []
            return

        col_count = max(len(r) for r in rows)
        # Pad short rows
        rows = [r + [""] * (col_count - len(r)) for r in rows]

        header = rows[0]
        data_rows = rows[1:]

        tbl_data = []
        # Header row
        tbl_data.append([Paragraph(fmt_inline(c), styles["th"]) for c in header])
        for row in data_rows:
            tbl_data.append([Paragraph(fmt_inline(c), styles["td"]) for c in row])

        avail = PAGE_W - 2 * MARGIN
        col_w = avail / col_count

        tbl = Table(tbl_data, colWidths=[col_w] * col_count, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  IITK_BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  WHITE),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0),  8.5),
            ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 8.5),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",         (0, 0), (-1, -1), 0.4, RULE_GREY),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("ROUNDEDCORNERS", [4]),
        ]))
        story.append(KeepTogether([tbl, Spacer(1, 8)]))
        in_table = False
        table_rows = []

    while i < len(lines):
        line = lines[i]

        # ── Code block ──────────────────────────────────────────────────────
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                # Render each line individually so the block can split across pages
                story.append(HRFlowable(width="100%", thickness=0.6,
                                        color=CODE_BORDER, spaceBefore=4, spaceAfter=0))
                for cl in code_lines:
                    story.append(Preformatted(cl if cl else " ", styles["code_block"]))
                story.append(HRFlowable(width="100%", thickness=0.6,
                                        color=CODE_BORDER, spaceBefore=0, spaceAfter=6))
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # ── Table row ────────────────────────────────────────────────────────
        if line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
            i += 1
            # Peek: if next line is not a table row, flush
            if i >= len(lines) or not lines[i].strip().startswith("|"):
                flush_table()
            continue
        elif in_table:
            flush_table()

        # ── Skip ToC entries (lines like "1. [text](#anchor)") ──────────────
        if re.match(r"^\d+\.\s+\[.*\]\(#.*\)\s*$", line.strip()):
            i += 1
            continue

        # ── Headings ─────────────────────────────────────────────────────────
        if line.startswith("#### "):
            text = fmt_inline(line[5:].strip())
            story.append(Paragraph(text, styles["h4"]))
            i += 1
            continue

        if line.startswith("### "):
            text = fmt_inline(line[4:].strip())
            story.append(Paragraph(text, styles["h3"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=RULE_GREY, spaceAfter=4))
            i += 1
            continue

        if line.startswith("## "):
            text = fmt_inline(line[3:].strip())
            story.append(Spacer(1, 4))
            story.append(Paragraph(text, styles["h2"]))
            i += 1
            continue

        if line.startswith("# "):
            text = fmt_inline(line[2:].strip())
            story.append(PageBreak())
            story.append(Paragraph(text, styles["h1"]))
            i += 1
            continue

        # ── Horizontal rule ──────────────────────────────────────────────────
        if re.match(r"^-{3,}\s*$", line) or re.match(r"^={3,}\s*$", line):
            story.append(HRFlowable(width="100%", thickness=0.8, color=RULE_GREY,
                                    spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # ── Bullet points ────────────────────────────────────────────────────
        m = re.match(r"^( {4}|\t)[-*] (.+)$", line)
        if m:
            text = fmt_inline(m.group(2))
            story.append(Paragraph(f"◦  {text}", styles["bullet2"]))
            i += 1
            continue

        m = re.match(r"^[-*] (.+)$", line)
        if m:
            text = fmt_inline(m.group(1))
            story.append(Paragraph(f"•  {text}", styles["bullet"]))
            i += 1
            continue

        # ── Numbered list ────────────────────────────────────────────────────
        m = re.match(r"^(\d+)\. (.+)$", line)
        if m:
            text = fmt_inline(m.group(2))
            story.append(Paragraph(f"{m.group(1)}.  {text}", styles["bullet"]))
            i += 1
            continue

        # ── Blank line ───────────────────────────────────────────────────────
        if line.strip() == "":
            story.append(Spacer(1, 4))
            i += 1
            continue

        # ── Normal paragraph ─────────────────────────────────────────────────
        text = fmt_inline(line.strip())
        if text:
            story.append(Paragraph(text, styles["body"]))
        i += 1

    if in_table:
        flush_table()

    return story


# ── Cover page ───────────────────────────────────────────────────────────────
def build_cover(styles):
    story = []
    story.append(Spacer(1, 2.5*cm))

    # Top accent bar (via a 1-row table acting as a colour block)
    bar = Table([[""]], colWidths=[PAGE_W - 2*MARGIN], rowHeights=[6])
    bar.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), IITK_BLUE)]))
    story.append(bar)
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph("Quetor", styles["title"]))
    story.append(Paragraph("A Web Service for Students Evaluation", styles["subtitle"]))
    story.append(Spacer(1, 0.3*cm))

    # Bottom accent bar
    story.append(bar)
    story.append(Spacer(1, 1.4*cm))

    story.append(Paragraph("Comprehensive Technical Project Report", styles["meta"]))
    story.append(Spacer(1, 1.2*cm))

    # Info box
    info = [
        ["Project Type",  "Undergraduate Project (UGP)"],
        ["Institute",     "Indian Institute of Technology Kanpur (IITK)"],
        ["Supervisor",    "Professor Shubham Sahay"],
        ["Developer 1",   "Snehasis Satapathy — Roll No. 221070"],
        ["Developer 2",   "Gautam Arora — Roll No. 220405"],
    ]
    s_key = ParagraphStyle("key", fontName="Helvetica-Bold", fontSize=10,
                           textColor=IITK_BLUE, leading=15)
    s_val = ParagraphStyle("val", fontName="Helvetica", fontSize=10,
                           textColor=BLACK, leading=15)
    tbl_data = [[Paragraph(k, s_key), Paragraph(v, s_val)] for k, v in info]
    tbl = Table(tbl_data, colWidths=[5.5*cm, PAGE_W - 2*MARGIN - 5.5*cm])
    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, WHITE]),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",            (0, 0), (-1, -1), 0.8, IITK_BLUE),
        ("LINEBELOW",      (0, 0), (-1, -2), 0.4, RULE_GREY),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 2*cm))

    story.append(Paragraph("IIT Kanpur · 2024–25", styles["meta"]))
    story.append(PageBreak())
    return story


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_path  = os.path.join(base_dir, "QUETOR_PROJECT_REPORT.md")
    pdf_path = os.path.join(base_dir, "QUETOR_PROJECT_REPORT.pdf")

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Strip the YAML-style title block at the very top (lines before first blank)
    # We'll render it as a proper cover page instead
    lines = md_text.splitlines()
    # Remove the first H1 and subtitle block (cover is rendered separately)
    # Find first '## ' heading and start body from there
    body_start = 0
    for idx, ln in enumerate(lines):
        if ln.startswith("## Table of Contents"):
            body_start = idx
            break
    body_md = "\n".join(lines[body_start:])

    styles = build_styles()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2.0*cm,
        bottomMargin=2.0*cm,
        title="Quetor — Project Report",
        author="Snehasis Satapathy & Gautam Arora",
        subject="UGP Technical Report — IIT Kanpur",
    )

    story = []
    story += build_cover(styles)
    story += parse_markdown(body_md, styles)

    doc.build(story, onFirstPage=make_page_decorator(), onLaterPages=make_page_decorator())
    print(f"PDF written → {pdf_path}")


if __name__ == "__main__":
    main()
