"""Generate the client-facing RA-04 bill PDF from the validated bill object."""

from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.clickup.ra_billing import load_ra04_bill


OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "Kaveri_SCP2_RA04_September_2026.pdf"


def money(value: Decimal) -> str:
    return f"INR{value: ,.2f}"


def qty(value: Decimal) -> str:
    return f"{value:g}"


def build_pdf(output_file: Path = OUTPUT_FILE) -> Path:
    bill = load_ra04_bill()
    totals = bill.totals

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20,
        spaceAfter=4 * mm,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=13,
        spaceAfter=5 * mm,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )

    small_style = ParagraphStyle(
        "SmallCustom",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Kaveri Infrasystems SCP2 RA-04",
        author="Kaveri Infrasystems",
    )

    story = []

    story.append(
        Paragraph(
            "KAVERI INFRASYSTEMS",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Smart Corridor Package 2 — RA-04 Bill",
            subtitle_style,
        )
    )

    header_data = [
        ["RA Number", "RA-04", "Work Month", "September 2026"],
        ["Project", "SCP2", "Reporting Date", "30 September 2026"],
    ]

    header_table = Table(
        header_data,
        colWidths=[28 * mm, 55 * mm, 32 * mm, 55 * mm],
    )

    header_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BACKGROUND", (2, 0), (2, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 3 * mm))

    story.append(
        Paragraph(
            "Bill Line Summary",
            section_style,
        )
    )

    boq_activity_map = {
        "B01": "A1010",
        "B02": "A2020",
        "B03": "A2030",
        "B04": "A3000 | A3010",
        "B05": "A3020",
        "B06": "A3030",
        "B07": "A4010",
    }

    line_data = [
        [
            "BOQ",
            "Description",
            "WBS / Activity",
            "Unit",
            "Contract Qty",
            "Prev. Billed",
            "Certified",
            "Disputed",
            "Billable",
            "Rate",
            "Gross",
        ]
    ]

    for line in bill.lines:
        line_data.append(
            [
                line.boq_item,
                Paragraph(
                    line.description,
                    small_style,
                ),
                boq_activity_map.get(
                    line.boq_item,
                    "NOT MAPPED",
                ),
                line.unit,
                qty(line.contract_qty),
                qty(line.previously_billed_qty),
                qty(line.period_certified_qty),
                qty(line.period_disputed_qty),
                qty(line.period_billable_qty),
                money(line.rate_inr),
                money(line.gross_value_inr),
            ]
        )

    line_table = Table(
        line_data,
        repeatRows=1,
        colWidths=[
            10 * mm,
            35 * mm,
            25 * mm,
            11 * mm,
            18 * mm,
            18 * mm,
            17 * mm,
            15 * mm,
            17 * mm,
            22 * mm,
            24 * mm,
        ],
    )

    line_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story.append(line_table)

    story.append(
        Paragraph(
            "Commercial Summary",
            section_style,
        )
    )

    summary_data = [
        ["Description", "Amount"],
        ["Contract Value", money(totals.contract_value_inr)],
        ["Gross Value", money(totals.gross_value_inr)],
        ["GST @ 18%", money(totals.gst_inr)],
        ["Retention @ 5%", money(totals.retention_inr)],
        ["Advance Recovery", money(totals.advance_recovery_inr)],
        ["Net Payable", money(totals.net_payable_inr)],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[115 * mm, 50 * mm],
        hAlign="RIGHT",
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(summary_table)

    story.append(
        Paragraph(
            "Mobilisation Advance",
            section_style,
        )
    )

    advance_data = [
        ["Description", "Amount"],
        [
            "Mobilisation Advance @ 8%",
            money(totals.mobilisation_advance_inr),
        ],
        [
            "Previous Advance Recovered",
            money(totals.previous_advance_recovered_inr),
        ],
        [
            "Outstanding Before RA-04",
            money(totals.outstanding_advance_before_ra04_inr),
        ],
        [
            "RA-04 Recovery",
            money(totals.advance_recovery_inr),
        ],
    ]

    advance_table = Table(
        advance_data,
        colWidths=[115 * mm, 50 * mm],
        hAlign="RIGHT",
    )

    advance_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(advance_table)

    story.append(
        Paragraph(
            "Exceptions and Notes",
            section_style,
        )
    )

    notes = []

    for line in bill.lines:
        if line.exclusion_reason:
            notes.append(
                f"{line.boq_item}: {line.exclusion_reason}"
            )

        if line.variation_qty:
            notes.append(
                f"{line.boq_item}: "
                f"{qty(line.variation_qty)} {line.unit} "
                "certified above contract quantity; "
                "recorded as variation."
            )

    if not notes:
        notes.append("No billing exceptions recorded.")

    notes_data = [
        [
            Paragraph(
                note,
                small_style,
            )
        ]
        for note in notes
    ]

    notes_table = Table(
        notes_data,
        colWidths=[165 * mm],
    )

    notes_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.4, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(notes_table)

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "Source: controlled project data pack and SCP2 schedule. "
            "All bill calculations are generated by the RA-04 bill engine.",
            small_style,
        )
    )

    document.build(story)

    return output_file


def main() -> None:
    output = build_pdf()
    print(f"RA-04 PDF created: {output}")


if __name__ == "__main__":
    main()