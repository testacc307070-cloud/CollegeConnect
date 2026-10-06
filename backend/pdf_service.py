"""
backend/pdf_service.py
Professional PDF Export Service for CollegeConnect Choice Optimizer.
Generates structured, print-ready A4 PDF documents using ReportLab.
"""

import io
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer line
        page_w, page_h = self._pagesize
        margin = 36
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(margin, 26, page_w - margin, 26)

        # Footer left & right
        footer_left = "CollegeConnect — TNEA Admissions Intelligence • Single-Window Choice Preparation (tneaonline.org)"
        footer_right = f"Page {self._pageNumber} of {total_pages}"

        self.drawString(margin, 16, footer_left)
        self.drawRightString(page_w - margin, 16, footer_right)

        self.restoreState()


def generate_choice_list_pdf(
    choices: List[Dict[str, Any]],
    student_profile: Optional[Dict[str, Any]] = None,
) -> io.BytesIO:
    """
    Generate an elegant, professional A4 landscape PDF for the student's choice list.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=38,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )
    timestamp_style = ParagraphStyle(
        "DocTimestamp",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#64748b"),
    )

    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    cell_regular = ParagraphStyle(
        "CellRegular",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    cell_center = ParagraphStyle(
        "CellCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#334155"),
    )
    cell_center_bold = ParagraphStyle(
        "CellCenterBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
    )
    th_style = ParagraphStyle(
        "THStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white,
    )

    story = []

    # 1. Header Banner
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    header_data = [
        [
            Paragraph("CollegeConnect — TNEA Admissions Preference List", title_style),
            Paragraph(f"Generated: {now_str}<br/>Status: Official Counseling Draft", timestamp_style),
        ],
        [
            Paragraph(
                "Tamil Nadu Engineering Admissions (TNEA 2026) • Strategy-Balanced Choice Order",
                subtitle_style,
            ),
            Paragraph("", subtitle_style),
        ]
    ]
    header_table = Table(header_data, colWidths=[520, 250])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. Student & Strategy Summary Box
    profile = student_profile or {}
    cutoff_val = profile.get("cutoff_mark")
    rank_val = profile.get("state_rank")
    comm_val = profile.get("community", "OC")
    quota_val = profile.get("quota", "GENERAL")

    cutoff_display = f"{float(cutoff_val):.2f} / 200.00" if cutoff_val else "Not Specified"
    rank_display = f"{int(rank_val):,}" if rank_val else "Not Specified"
    quota_display = "7.5% Govt School Quota" if "7_5" in str(quota_val).upper() else ("Special Quota" if "SPECIAL" in str(quota_val).upper() else "General Academic")

    # Count tiers in choices
    total_choices = len(choices)
    safe_cnt = sum(1 for c in choices if str(c.get("tier", "")).lower() == "safe")
    target_cnt = sum(1 for c in choices if str(c.get("tier", "")).lower() == "target")
    reach_cnt = sum(1 for c in choices if str(c.get("tier", "")).lower() == "reach")

    safe_pct = round(safe_cnt / total_choices * 100) if total_choices else 0
    target_pct = round(target_cnt / total_choices * 100) if total_choices else 0
    reach_pct = round(reach_cnt / total_choices * 100) if total_choices else 0

    strategy_text = f"<b>{reach_cnt}</b> Reach ({reach_pct}%) • <b>{target_cnt}</b> Target ({target_pct}%) • <b>{safe_cnt}</b> Safe ({safe_pct}%)"

    summary_data = [
        [
            Paragraph("<b>Candidate Profile:</b>", cell_bold),
            Paragraph(f"Cutoff: <b>{cutoff_display}</b>", cell_regular),
            Paragraph(f"State Rank: <b>{rank_display}</b>", cell_regular),
            Paragraph(f"Community: <b>{comm_val}</b>", cell_regular),
            Paragraph(f"Counseling Quota: <b>{quota_display}</b>", cell_regular),
        ],
        [
            Paragraph("<b>Strategy Balance:</b>", cell_bold),
            Paragraph(f"Total Choices: <b>{total_choices}</b>", cell_regular),
            Paragraph(strategy_text, cell_regular),
            Paragraph("Recommended: 20% Reach / 50% Target / 30% Safe", cell_regular),
            Paragraph("Source: TNEA 2021–2025 Historical Records", cell_regular),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[110, 160, 170, 160, 170])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # 3. Main Choice Table
    table_headers = [
        Paragraph("Pref", th_style),
        Paragraph("Code", th_style),
        Paragraph("College Name", th_style),
        Paragraph("Branch / Discipline", th_style),
        Paragraph("District", th_style),
        Paragraph("2025 Benchmark", th_style),
        Paragraph("Feasibility", th_style),
        Paragraph("Est. Prob.", th_style),
    ]

    table_rows = [table_headers]

    for idx, c in enumerate(choices, start=1):
        pref_no = str(idx)
        c_code = str(c.get("college_code", "—"))
        c_name = str(c.get("college_name", f"College {c_code}"))
        b_code = str(c.get("branch_code", "—"))
        b_name = str(c.get("branch_name", b_code))
        district = str(c.get("district", "—"))

        cut_val = c.get("latest_cutoff")
        cut_str = f"{float(cut_val):.2f}" if cut_val is not None else "—"
        rnk_val = c.get("latest_closing_rank")
        rnk_str = f"Rank {int(rnk_val):,}" if rnk_val is not None else ""
        benchmark_str = f"{cut_str}<br/>{rnk_str}" if rnk_str else cut_str

        tier = str(c.get("tier", "Target")).capitalize()
        tier_color = "#059669" if tier == "Safe" else ("#2563eb" if tier == "Target" else "#7c3aed")
        tier_bg = "#ecfdf5" if tier == "Safe" else ("#eff6ff" if tier == "Target" else "#f5f3ff")
        tier_html = f"<font color='{tier_color}'><b>{tier}</b></font>"

        prob = c.get("estimated_probability")
        prob_str = f"{float(prob):.1f}%" if prob is not None else "—"

        table_rows.append([
            Paragraph(f"<b>{pref_no}</b>", cell_center_bold),
            Paragraph(c_code, cell_center),
            Paragraph(f"<b>{c_name}</b>", cell_regular),
            Paragraph(f"<b>{b_code}</b> - {b_name}", cell_regular),
            Paragraph(district, cell_regular),
            Paragraph(benchmark_str, cell_center),
            Paragraph(tier_html, cell_center),
            Paragraph(prob_str, cell_center_bold),
        ])

    # Col Widths total: 30 + 40 + 235 + 205 + 75 + 85 + 55 + 45 = 770 pt (matches A4 landscape printable width)
    col_widths = [30, 40, 235, 205, 75, 85, 55, 45]
    main_table = Table(table_rows, colWidths=col_widths, repeatRows=1)

    t_style = [
        # Table Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        # Table Borders
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]

    # Alternating row colors
    for r_idx in range(1, len(table_rows)):
        bg_col = colors.HexColor("#f8fafc") if r_idx % 2 == 1 else colors.white
        t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), bg_col))

    main_table.setStyle(TableStyle(t_style))
    story.append(main_table)

    # 4. Advisory Note Footer
    story.append(Spacer(1, 10))
    note_text = (
        "<b>Important Instructions for DoTE Portal Entry:</b> "
        "Log in to <i>tneaonline.org</i> during your allocated counseling round. "
        "Enter your choices exactly following this preference order. There is no limit on the number of choices you can register. "
        "Ensure you include sufficient 'Safe' choices as backup allotments."
    )
    story.append(Paragraph(note_text, subtitle_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
