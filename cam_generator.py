"""
CreditIQ — CAM PDF Generator
Generates a professional Credit Appraisal Memorandum as PDF.
Uses ReportLab (pip install reportlab).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import io


# ── Brand colours ──
EMERALD  = colors.HexColor("#059669")
DARK     = colors.HexColor("#1C1C1E")
AMBER    = colors.HexColor("#D97706")
RED_CLR  = colors.HexColor("#DC2626")
LIGHT_BG = colors.HexColor("#F5F7FA")
MUTED    = colors.HexColor("#6B7280")
WHITE    = colors.white


def _risk_color(risk: str):
    if risk in ("LOW",):        return EMERALD
    if risk in ("MEDIUM",):     return AMBER
    return RED_CLR


def generate_cam_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"CAM — {data.get('company_name', 'Report')}",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    h1 = ParagraphStyle("H1", parent=styles["Normal"],
        fontSize=22, fontName="Helvetica-Bold", textColor=DARK,
        spaceAfter=4, spaceBefore=16)
    h2 = ParagraphStyle("H2", parent=styles["Normal"],
        fontSize=13, fontName="Helvetica-Bold", textColor=EMERALD,
        spaceAfter=4, spaceBefore=12)
    body = ParagraphStyle("Body", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", textColor=DARK,
        leading=16, spaceAfter=4)
    muted_style = ParagraphStyle("Muted", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica", textColor=MUTED, leading=14)
    bold_body = ParagraphStyle("BoldBody", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold", textColor=DARK)

    story = []

    # ── Header ────────────────────────────────────────────
    company = data.get("company_name", "Company")
    today   = datetime.now().strftime("%d %B %Y")
    risk    = data.get("risk_band", "MEDIUM")
    decision= data.get("decision", "REVIEW")
    w_score = data.get("weighted_score", 0)
    rec_lim = data.get("recommended_limit", 0)
    rate    = data.get("interest_rate", "MCLR + 2%")
    tenor   = data.get("tenor_months", 60)
    rationale = data.get("rationale", "")

    # Title box
    title_data = [[
        Paragraph(f"<b>CREDIT APPRAISAL MEMORANDUM</b>", ParagraphStyle("TH",
            fontSize=16, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_LEFT)),
        Paragraph(f"<b>{decision}</b>", ParagraphStyle("TD",
            fontSize=14, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_RIGHT)),
    ]]
    title_table = Table(title_data, colWidths=["70%", "30%"])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("TOPPADDING",  (0,0), (-1,-1), 12),
        ("BOTTOMPADDING",(0,0), (-1,-1), 12),
        ("LEFTPADDING", (0,0), (-1,-1), 14),
        ("RIGHTPADDING",(0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 8))

    # Meta row
    meta_data = [[
        Paragraph(f"<b>{company}</b>", ParagraphStyle("Met", fontSize=14,
            fontName="Helvetica-Bold", textColor=DARK)),
        Paragraph(f"Date: {today}", muted_style),
        Paragraph(f"Score: <b>{w_score}/100</b>", ParagraphStyle("Sc",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=_risk_color(risk))),
        Paragraph(f"Risk: <b>{risk}</b>", ParagraphStyle("Ri",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=_risk_color(risk))),
    ]]
    meta_table = Table(meta_data, colWidths=["40%", "20%", "20%", "20%"])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BG),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ── Section 1: Borrower Details ──────────────────────
    story.append(Paragraph("1. Borrower Details", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EMERALD, spaceAfter=6))

    borrow_rows = [
        ["Company Name", company],
        ["Sector", data.get("sector", "—")],
        ["Loan Requested", f"₹{data.get('loan_ask','—')} Crore for {tenor} months"],
        ["CIN", data.get("cin", "—")],
        ["GST Number", data.get("gst_number", "—")],
    ]
    _add_kv_table(story, borrow_rows)
    story.append(Spacer(1, 10))

    # ── Section 2: Financial Highlights ──────────────────
    story.append(Paragraph("2. Financial Highlights (FY2024)", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EMERALD, spaceAfter=6))

    derived = data.get("derived", {})
    fin_rows = [
        ["Revenue",        f"₹{data.get('revenue','—')} Crore",
         "EBITDA Margin",  f"{derived.get('ebitda_margin','—')}%"],
        ["PAT",            f"₹{data.get('pat','—')} Crore",
         "Debt / Equity",  f"{derived.get('de_ratio','—')}x"],
        ["Net Worth",      f"₹{data.get('net_worth','—')} Crore",
         "DSCR",           f"{data.get('dscr','—')}x"],
        ["Total Debt",     f"₹{data.get('total_debt','—')} Crore",
         "GST Variance",   f"{derived.get('gst_variance','—')}%"],
    ]
    _add_4col_table(story, fin_rows)
    story.append(Spacer(1, 10))

    # ── Section 3: Five-Cs Scorecard ─────────────────────
    story.append(Paragraph("3. Five-Cs Scorecard", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EMERALD, spaceAfter=6))

    scores   = data.get("scores", {})
    evidence = data.get("evidence", [])

    hdr = [
        Paragraph("<b>Criterion</b>", bold_body),
        Paragraph("<b>Score</b>",     bold_body),
        Paragraph("<b>Weight</b>",    bold_body),
        Paragraph("<b>Weighted</b>",  bold_body),
        Paragraph("<b>Key Evidence</b>", bold_body),
    ]
    score_rows = [hdr]
    c_map = [
        ("Character",  "character",  0.25),
        ("Capacity",   "capacity",   0.30),
        ("Capital",    "capital",    0.20),
        ("Collateral", "collateral", 0.15),
        ("Conditions", "conditions", 0.10),
    ]
    for name, key, wt in c_map:
        sc = scores.get(key, 0)
        ev = next((e for e in evidence if e["criterion"] == name), {})
        trace_text = "; ".join(ev.get("trace", [])[:2]) if ev else ""
        score_rows.append([
            Paragraph(name, body),
            Paragraph(f"<b>{sc}/100</b>", ParagraphStyle("SC2",
                fontSize=10, fontName="Helvetica-Bold",
                textColor=_risk_color("LOW" if sc >= 75 else "MEDIUM" if sc >= 60 else "HIGH"))),
            Paragraph(f"{int(wt*100)}%", body),
            Paragraph(f"{round(sc * wt, 1)}", body),
            Paragraph(trace_text[:120], muted_style),
        ])

    # Total row
    score_rows.append([
        Paragraph("<b>TOTAL</b>", bold_body),
        Paragraph(f"<b>{w_score}/100</b>", ParagraphStyle("WT",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=_risk_color(risk))),
        Paragraph("100%", body),
        Paragraph(f"<b>{w_score}</b>", bold_body),
        Paragraph(f"<b>{risk} RISK</b>", ParagraphStyle("RB",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=_risk_color(risk))),
    ])

    score_table = Table(score_rows, colWidths=["18%","12%","10%","12%","48%"])
    score_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-2), [WHITE, LIGHT_BG]),
        ("BACKGROUND",    (0,-1),(-1,-1), colors.HexColor("#E6FAF2")),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    # ── Section 4: Risk Flags ────────────────────────────
    story.append(Paragraph("4. Risk Flags", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EMERALD, spaceAfter=6))

    flags = data.get("flags", [])
    if flags:
        flag_hdr = [
            Paragraph("<b>Issue</b>",  bold_body),
            Paragraph("<b>Detail</b>", bold_body),
            Paragraph("<b>Level</b>",  bold_body),
        ]
        flag_rows = [flag_hdr]
        for f in flags:
            lv_col = RED_CLR if f["level"] == "HIGH" else AMBER
            flag_rows.append([
                Paragraph(f.get("issue",  f.get("text","")), body),
                Paragraph(f.get("amount", ""), muted_style),
                Paragraph(f"<b>{f['level']}</b>", ParagraphStyle("FL",
                    fontSize=10, fontName="Helvetica-Bold", textColor=lv_col)),
            ])
        flag_table = Table(flag_rows, colWidths=["45%", "35%", "20%"])
        flag_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), DARK),
            ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_BG]),
            ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#E5E7EB")),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ]))
        story.append(flag_table)
    else:
        story.append(Paragraph("No significant risk flags identified.", body))
    story.append(Spacer(1, 10))

    # ── Section 5: Recommendation ────────────────────────
    story.append(Paragraph("5. Recommendation & Sanction Terms", h2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EMERALD, spaceAfter=6))

    dec_color = EMERALD if "APPROVE" in decision and "REJECT" not in decision else RED_CLR
    rec_rows = [
        ["Decision",          decision],
        ["Sanctioned Limit",  f"₹{rec_lim} Crore" if rec_lim > 0 else "Nil"],
        ["Interest Rate",     rate],
        ["Tenor",             f"{tenor} months"],
        ["Risk Band",         risk],
    ]
    _add_kv_table(story, rec_rows, accent_col=0)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Decision Rationale:</b>", bold_body))
    story.append(Paragraph(rationale, body))
    story.append(Spacer(1, 8))

    if rec_lim > 0:
        conditions = [
            "Quarterly DSCR monitoring — minimum 1.25x covenant",
            "GST variance to be resolved / explained within 90 days of disbursement",
            "Any further promoter share pledge requires prior bank approval",
            "Annual review of financials; CAM to be refreshed every 12 months",
        ]
        story.append(Paragraph("<b>Key Conditions:</b>", bold_body))
        for c in conditions:
            story.append(Paragraph(f"• {c}", body))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceAfter=4))
    story.append(Paragraph(
        f"Generated by CreditIQ Platform &nbsp;·&nbsp; {today} &nbsp;·&nbsp; CONFIDENTIAL",
        ParagraphStyle("Footer", fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()


# ── Helpers ───────────────────────────────────────────────

def _add_kv_table(story, rows, accent_col=None):
    tdata = []
    for k, v in rows:
        tdata.append([
            Paragraph(str(k), ParagraphStyle("KV_K", fontSize=10,
                fontName="Helvetica-Bold", textColor=MUTED)),
            Paragraph(str(v), ParagraphStyle("KV_V", fontSize=10,
                fontName="Helvetica", textColor=DARK)),
        ])
    t = Table(tdata, colWidths=["35%", "65%"])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, LIGHT_BG]),
        ("GRID",           (0,0), (-1,-1), 0.4, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(t)


def _add_4col_table(story, rows):
    styles = getSampleStyleSheet()
    body = ParagraphStyle("B2", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica", textColor=DARK)
    bold = ParagraphStyle("B3", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold", textColor=MUTED)
    tdata = []
    for row in rows:
        tdata.append([
            Paragraph(str(row[0]), bold),
            Paragraph(str(row[1]), body),
            Paragraph(str(row[2]), bold),
            Paragraph(str(row[3]), body),
        ])
    t = Table(tdata, colWidths=["20%", "30%", "20%", "30%"])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, LIGHT_BG]),
        ("GRID",           (0,0), (-1,-1), 0.4, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(t)
