"""
This file assembles project results and evidence into the final assignment PDF.
We need it to turn the separate reports, tables, and screenshots into one document for review and submission.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    NextPageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.utils import ImageReader

# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
FINAL_DIR = ROOT / "final"
OUTPUT = FINAL_DIR / "Delipat_Assignment_Three_Final_Submission.pdf"

BUILD_LOG = ROOT / "BUILD_LOG.md"
FEASIBILITY = ROOT / "FEASIBILITY.md"


# ============================================================
# DESIGN COLORS
# ============================================================

NAVY = colors.HexColor("#123B5D")
NAVY_DARK = colors.HexColor("#0B2A43")

TEAL = colors.HexColor("#168A8A")
TEAL_LIGHT = colors.HexColor("#E8F5F5")

BLUE_LIGHT = colors.HexColor("#EEF4F8")

GRAY_BG = colors.HexColor("#F5F7F9")
GRAY_BORDER = colors.HexColor("#D5DDE5")
GRAY_TEXT = colors.HexColor("#52606D")

BLACK = colors.HexColor("#17202A")
WHITE = colors.white

AMBER = colors.HexColor("#9A6700")
RED = colors.HexColor("#A33A3A")


# ============================================================
# REQUIRED SCREENSHOTS
# ============================================================

SCREENSHOT_FILES = [
    (
        "01",
        "ClickUp Workspace — Schedule & WBS",
        "01_clickup_workspace_schedule_wbs.png",
    ),
    (
        "02",
        "Imported P6 Schedule Activities and Milestones",
        "02_clickup_imported_activities.png",
    ),
    (
        "03",
        "ClickUp RA Billing List",
        "03_ra_billing_list.png",
    ),
    (
        "04",
        "RA-04 — September 2026",
        "04_ra04_task.png",
    ),
    (
        "05",
        "RA-04 PDF Bill",
        "05_ra04_pdf.png",
    ),
    (
        "06",
        "Purchase Approval Router",
        "06_purchase_approval_router.png",
    ),
    (
        "07",
        "Cash-flow Forecast",
        "07_cashflow_forecast.png",
    ),
    (
        "08",
        "Weekly Management Report",
        "08_weekly_management_report.png",
    ),
    (
        "09",
        "Local Ollama Accuracy",
        "09_local_ollama_accuracy.png",
    ),
    (
        "10",
        "Automated Tests",
        "10_automated_tests.png",
    ),
    (
        "11",
        "GitHub Repository",
        "11_github_repository.png",
    ),
    (
        "12",
        "Feasibility Verdicts",
        "12_feasibility_verdicts.png",
    ),
]


# ============================================================
# FONT SETUP
# ============================================================


"""
Finds an installed font from preferred choices so the PDF stays readable across different computers.
"""


def find_font(names):
    locations = [
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/noto"),
        Path("/usr/share/fonts/opentype/noto"),
    ]

    for directory in locations:
        if not directory.exists():
            continue

        for name in names:
            candidate = directory / name

            if candidate.exists():
                return candidate

    return None


regular_font = find_font(
    [
        "DejaVuSans.ttf",
        "NotoSans-Regular.ttf",
        "arial.ttf",
    ]
)

bold_font = find_font(
    [
        "DejaVuSans-Bold.ttf",
        "NotoSans-Bold.ttf",
        "arialbd.ttf",
    ]
)


if regular_font and bold_font:
    pdfmetrics.registerFont(
        TTFont(
            "ReportFont",
            str(regular_font),
        )
    )

    pdfmetrics.registerFont(
        TTFont(
            "ReportFontBold",
            str(bold_font),
        )
    )

    FONT = "ReportFont"
    FONT_BOLD = "ReportFontBold"

else:
    FONT = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()


styles.add(
    ParagraphStyle(
        name="BodyCustom",
        fontName=FONT,
        fontSize=9.3,
        leading=14,
        textColor=BLACK,
        spaceAfter=6,
    )
)


styles.add(
    ParagraphStyle(
        name="SmallCustom",
        fontName=FONT,
        fontSize=7.8,
        leading=10.5,
        textColor=GRAY_TEXT,
        spaceAfter=3,
    )
)


styles.add(
    ParagraphStyle(
        name="TableHeaderCustom",
        fontName=FONT_BOLD,
        fontSize=7.7,
        leading=10,
        textColor=WHITE,
    )
)


styles.add(
    ParagraphStyle(
        name="TableCellCustom",
        fontName=FONT,
        fontSize=7.7,
        leading=10,
        textColor=BLACK,
    )
)


styles.add(
    ParagraphStyle(
        name="CoverTitleCustom",
        fontName=FONT_BOLD,
        fontSize=25,
        leading=30,
        textColor=NAVY,
        alignment=TA_CENTER,
    )
)


styles.add(
    ParagraphStyle(
        name="CoverSubtitleCustom",
        fontName=FONT,
        fontSize=12,
        leading=18,
        textColor=GRAY_TEXT,
        alignment=TA_CENTER,
    )
)


styles.add(
    ParagraphStyle(
        name="HeroCustom",
        fontName=FONT_BOLD,
        fontSize=14,
        leading=19,
        textColor=NAVY,
        alignment=TA_CENTER,
    )
)


styles.add(
    ParagraphStyle(
        name="EvidenceCaption",
        fontName=FONT,
        fontSize=7.2,
        leading=9,
        textColor=GRAY_TEXT,
        alignment=TA_CENTER,
    )
)


# ============================================================
# BASIC HELPERS
# ============================================================


"""
Escapes special HTML characters so report text is displayed literally instead of being treated as markup.
"""


def escape_text(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


"""
Creates a consistently styled paragraph so report text follows the document's typography.
"""


def paragraph(
    text,
    style="BodyCustom",
):
    return Paragraph(
        escape_text(text).replace(
            "\n",
            "<br/>",
        ),
        styles[style],
    )


"""
Creates a paragraph that supports ReportLab markup so selected text can receive emphasis or color.
"""


def rich_paragraph(
    text,
    style="BodyCustom",
):
    return Paragraph(
        text,
        styles[style],
    )


"""
Formats an amount as Indian rupees so financial figures are easy to scan.
"""


def money(value):
    return f"INR {value:,.2f}"


"""
Creates a styled bullet item so report lists remain consistent and readable.
"""


def bullet(text):
    return rich_paragraph(
        f'<font color="#168A8A">●</font> ' f"{escape_text(text)}",
        "BodyCustom",
    )


# ============================================================
# INPUT VALIDATION
# ============================================================


"""
Checks required source files and evidence before PDF generation so missing inputs are found early.
"""


def validate_inputs():

    errors = []

    if not BUILD_LOG.exists():
        errors.append(f"Missing BUILD_LOG.md: {BUILD_LOG}")

    if not FEASIBILITY.exists():
        errors.append(f"Missing FEASIBILITY.md: {FEASIBILITY}")

    if not SCREENSHOTS.exists():
        errors.append(f"Missing screenshots directory: {SCREENSHOTS}")

    for _, _, filename in SCREENSHOT_FILES:

        path = SCREENSHOTS / filename

        if not path.exists():
            errors.append(f"Missing screenshot: {filename}")

    if errors:

        print()
        print("INPUT VALIDATION FAILED")
        print()

        for error in errors:
            print(" -", error)

        raise SystemExit(1)

    print("Input validation: PASS")
    print("  BUILD_LOG.md: present")
    print("  FEASIBILITY.md: present")
    print("  Screenshots: 12/12 present")


# ============================================================
# SECTION HEADER
# ============================================================


"""
Builds a numbered section heading so readers can navigate the report more easily.
"""


def section_header(
    number,
    title,
    total_width=160 * mm,
):

    number_style = ParagraphStyle(
        f"SectionNumber_{number}_{total_width}",
        fontName=FONT_BOLD,
        fontSize=10,
        leading=12,
        textColor=WHITE,
        alignment=TA_CENTER,
    )

    title_style = ParagraphStyle(
        f"SectionTitle_{number}_{total_width}",
        fontName=FONT_BOLD,
        fontSize=15,
        leading=19,
        textColor=NAVY,
    )

    number_width = 15 * mm
    title_width = total_width - number_width

    table = Table(
        [
            [
                Paragraph(
                    escape_text(number),
                    number_style,
                ),
                Paragraph(
                    escape_text(title),
                    title_style,
                ),
            ]
        ],
        colWidths=[
            number_width,
            title_width,
        ],
        rowHeights=[12 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    NAVY,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    BLUE_LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    NAVY,
                ),
                (
                    "LINEBELOW",
                    (1, 0),
                    (1, 0),
                    2,
                    TEAL,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


# ============================================================
# TABLE
# ============================================================


"""
Builds a formatted table from report data so related values can be compared clearly.
"""


def make_table(
    data,
    widths,
    header=True,
):

    rows = []

    for row_number, row in enumerate(data):

        converted = []

        for cell in row:

            if isinstance(
                cell,
                Paragraph,
            ):

                converted.append(cell)

            else:

                if header and row_number == 0:
                    style = "TableHeaderCustom"

                else:
                    style = "TableCellCustom"

                converted.append(
                    paragraph(
                        cell,
                        style,
                    )
                )

        rows.append(converted)

    table = Table(
        rows,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    commands = [
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.45,
            GRAY_BORDER,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            6,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            6,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
    ]

    if header:

        commands.extend(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
            ]
        )

        for row_number in range(
            1,
            len(rows),
        ):

            if row_number % 2 == 0:

                commands.append(
                    (
                        "BACKGROUND",
                        (0, row_number),
                        (-1, row_number),
                        GRAY_BG,
                    )
                )

    table.setStyle(TableStyle(commands))

    return table


# ============================================================
# INFORMATION BOX
# ============================================================


"""
Builds a highlighted information box so important notes and exceptions stand out.
"""


def info_box(
    title,
    text,
    color=TEAL,
    width=160 * mm,
):

    content = [
        [
            rich_paragraph(
                f'<font color="{color.hexval()}">'
                f"<b>{escape_text(title)}</b>"
                f"</font><br/>"
                f"{escape_text(text)}",
                "BodyCustom",
            )
        ]
    ]

    table = Table(
        content,
        colWidths=[width],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    TEAL_LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    color,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


# ============================================================
# PAGE SIZES
# ============================================================

PORTRAIT = A4
LANDSCAPE = landscape(A4)


# ============================================================
# PORTRAIT PAGE HEADER / FOOTER
# ============================================================


"""
Draws common page details for portrait pages so headers, footers, and numbering stay consistent.
"""


def portrait_page(
    canvas,
    doc,
):

    canvas.saveState()

    width, height = PORTRAIT

    # Top accent line
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(1.2)

    canvas.line(
        18 * mm,
        height - 12 * mm,
        width - 18 * mm,
        height - 12 * mm,
    )

    # Bottom line
    canvas.setStrokeColor(GRAY_BORDER)

    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        13 * mm,
        width - 18 * mm,
        13 * mm,
    )

    # Footer
    canvas.setFont(
        FONT,
        7,
    )

    canvas.setFillColor(GRAY_TEXT)

    canvas.drawString(
        18 * mm,
        8 * mm,
        "Delipat Assignment 3  •  " "Kaveri Infrasystems  •  SCP2",
    )

    canvas.drawRightString(
        width - 18 * mm,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# LANDSCAPE PAGE HEADER / FOOTER
# ============================================================


"""
Draws common page details for landscape pages so wide tables keep the same document framing.
"""


def landscape_page(
    canvas,
    doc,
):

    canvas.saveState()

    width, height = LANDSCAPE

    # Top accent line
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(1.2)

    canvas.line(
        14 * mm,
        height - 10 * mm,
        width - 14 * mm,
        height - 10 * mm,
    )

    # Bottom line
    canvas.setStrokeColor(GRAY_BORDER)

    canvas.setLineWidth(0.5)

    canvas.line(
        14 * mm,
        10 * mm,
        width - 14 * mm,
        10 * mm,
    )

    canvas.setFont(
        FONT,
        7,
    )

    canvas.setFillColor(GRAY_TEXT)

    canvas.drawString(
        14 * mm,
        6 * mm,
        "Delipat Assignment 3  •  " "Kaveri Infrasystems  •  SCP2",
    )

    canvas.drawRightString(
        width - 14 * mm,
        6 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# IMAGE HANDLING
# ============================================================


"""
Reads image dimensions so evidence can be fitted to the page without changing its proportions.
"""


def image_size(path):

    reader = ImageReader(str(path))

    return reader.getSize()


"""
Chooses a page orientation from an image's shape so each screenshot has suitable space.
"""


def evidence_orientation(path):

    width, height = image_size(path)

    # Tall screenshots remain portrait.
    #
    # Wide screenshots become landscape.
    #
    # This prevents tall evidence such as the
    # feasibility screenshot from becoming tiny.

    if height > width * 1.15:
        return "portrait"

    return "landscape"


"""
Creates a fitted image element so evidence remains legible and keeps its original proportions.
"""


def evidence_image(
    path,
    orientation,
):

    width, height = image_size(path)

    if orientation == "landscape":

        max_width = 265 * mm

        # Deliberately kept below the full frame height
        # so that title + screenshot + caption fit
        # on exactly one page.
        max_height = 145 * mm

    else:

        max_width = 175 * mm
        max_height = 220 * mm

    scale = min(
        max_width / width,
        max_height / height,
    )

    return Image(
        str(path),
        width=width * scale,
        height=height * scale,
        hAlign="CENTER",
    )


# ============================================================
# EVIDENCE PAGE
# ============================================================


"""
Adds a numbered evidence item and caption so screenshots can be identified and referenced.
"""


def add_evidence(
    story,
    number,
    title,
    filename,
):

    path = SCREENSHOTS / filename

    if not path.exists():

        raise FileNotFoundError(f"Evidence screenshot not found: {path}")

    orientation = evidence_orientation(path)

    if orientation == "landscape":

        template_name = "evidence_landscape"

        header_width = 265 * mm

    else:

        template_name = "evidence_portrait"

        header_width = 175 * mm

    # Switch orientation BEFORE creating
    # the evidence page.
    story.append(NextPageTemplate(template_name))

    story.append(PageBreak())

    story.append(
        section_header(
            f"9.{number}",
            title,
            total_width=header_width,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        evidence_image(
            path,
            orientation,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        paragraph(
            f"Evidence {number}/12  •  " f"screenshots/{filename}",
            "EvidenceCaption",
        )
    )


# ============================================================
# BUILD PDF STORY
# ============================================================


"""
Assembles report sections, tables, and evidence in order so the PDF presents a complete project narrative.
"""


def build_story():

    story = []

    # Always start in portrait.
    story.append(NextPageTemplate("portrait"))

    # ========================================================
    # COVER
    # ========================================================

    story.append(
        Spacer(
            1,
            42 * mm,
        )
    )

    story.append(
        paragraph(
            "DELIPAT IT — ASSIGNMENT 3",
            "CoverTitleCustom",
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        paragraph(
            "Live Implementation & Feasibility Submission",
            "CoverSubtitleCustom",
        )
    )

    story.append(
        Spacer(
            1,
            12 * mm,
        )
    )

    story.append(
        paragraph(
            "Kaveri Infrasystems — Smart Corridor Package 2",
            "HeroCustom",
        )
    )

    story.append(
        paragraph(
            "Project SCP2  •  " "Reporting date 30 September 2026",
            "CoverSubtitleCustom",
        )
    )

    story.append(
        Spacer(
            1,
            12 * mm,
        )
    )

    cover_data = [
        [
            "Submission",
            "Assignment 3",
        ],
        [
            "Repository",
            "zahir2003/delipat-assignment-three-kaveri",
        ],
        [
            "Verified commit",
            "94da43c",
        ],
        [
            "Automated tests",
            "22 / 22 passed",
        ],
        [
            "Evidence",
            "12 / 12 screenshots",
        ],
    ]

    story.append(
        make_table(
            cover_data,
            [
                50 * mm,
                110 * mm,
            ],
            header=False,
        )
    )

    story.append(
        Spacer(
            1,
            13 * mm,
        )
    )

    story.append(
        info_box(
            "Submission scope",
            "Working implementation, project-control evidence, "
            "AI evaluation, ClickUp verification and F1–F13 "
            "feasibility assessment.",
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 1
    # ========================================================

    story.append(
        section_header(
            "1",
            "Submission Summary",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "This submission implements the four required "
            "deterministic programs, documents the ClickUp "
            "control model, evaluates local Ollama against "
            "hand-labelled execution remarks, verifies "
            "ClickUp AI answers against computed project "
            "figures, and records the feasibility of F1–F13.",
        )
    )

    summary_data = [
        [
            "Area",
            "Implementation / Evidence",
        ],
        [
            "Schedule importer",
            "Idempotent XER import with " "WBS/activity relationships",
        ],
        [
            "RA bill engine",
            "RA-04 September 2026 " "calculation and ClickUp record",
        ],
        [
            "Approval router",
            "Value-based approval, escalation " "and anti-splitting",
        ],
        [
            "Cashflow forecaster",
            "October–December 2026 " "controlled forecast",
        ],
        [
            "Local AI",
            "Ollama classification over " "all 26 execution remarks",
        ],
        [
            "ClickUp AI",
            "Six required project questions verified",
        ],
        [
            "Weekly report",
            "Deterministic numbers with " "local-AI narrative",
        ],
        [
            "Feasibility",
            "F1–F13 bucketed across the " "four required feasibility buckets",
        ],
        [
            "Evidence",
            "12 screenshots plus " "public GitHub repository",
        ],
    ]

    story.append(
        make_table(
            summary_data,
            [
                45 * mm,
                115 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        info_box(
            "Controlled-data principle",
            "Contract values, rates, project calculations and "
            "management numbers are generated from controlled "
            "project data. External AI is not used for calculations. "
            "The local Ollama narrative layer is restricted to "
            "supplied deterministic report values.",
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 2
    # ========================================================

    story.append(
        section_header(
            "2",
            "Dated Build / Implementation Log",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    build_data = [
        [
            "Build date",
            "27 September 2026",
        ],
        [
            "Build time",
            "20:55:37 IST",
        ],
        [
            "Repository",
            "zahir2003/delipat-assignment-three-kaveri",
        ],
        [
            "Current verified commit",
            "94da43c",
        ],
        [
            "Automated tests",
            "22 / 22 passed",
        ],
    ]

    story.append(
        make_table(
            build_data,
            [
                55 * mm,
                105 * mm,
            ],
            header=False,
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        paragraph(
            "The dated build log documents the implementation "
            "verification performed on 27 September 2026. "
            "The repository was subsequently finalized with "
            "documentation and evidence changes and verified "
            "at commit 94da43c.",
        )
    )

    story.append(
        paragraph(
            "Implemented components",
            "HeroCustom",
        )
    )

    components = [
        "Local Ollama execution-log extraction.",
        "Idempotent Primavera P6 XER schedule importer.",
        "RA-04 bill engine and ClickUp billing record.",
        "Purchase approval router with leave escalation " "and anti-splitting.",
        "WBS-based cashflow forecaster.",
        "Weekly management report.",
        "Local Ollama management narrative.",
        "ClickUp schedule and RA billing evidence.",
        "F1–F13 feasibility assessment.",
        "Automated test suite and evidence screenshots.",
    ]

    for item in components:
        story.append(bullet(item))

    story.append(PageBreak())

    # ========================================================
    # SECTION 3 — RA-04
    # ========================================================

    story.append(
        section_header(
            "3",
            "RA-04 — September 2026 Billing",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "RA-04 is calculated from the controlled contract, "
            "cumulative billing, September measurements, "
            "production/QC records and the stated "
            "mobilisation-recovery policy.",
        )
    )

    ra_data = [
        [
            "BOQ",
            "Billable Qty",
            "Rate",
            "Gross",
            "Control",
        ],
        [
            "B02",
            "1,500 m",
            money(1150),
            money(1725000),
            "300 m failed QC excluded",
        ],
        [
            "B03",
            "24 nos",
            money(38500),
            money(924000),
            "2 nos failed QC excluded",
        ],
        [
            "B04",
            "4.9 km",
            money(185000),
            money(906500),
            "0.3 km disputed",
        ],
        [
            "B05",
            "700 m",
            money(220),
            money(154000),
            "250 m variation",
        ],
        [
            "B06",
            "12 nos",
            money(14500),
            money(174000),
            "2 disputed excluded",
        ],
    ]

    story.append(
        make_table(
            ra_data,
            [
                18 * mm,
                29 * mm,
                31 * mm,
                35 * mm,
                47 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    totals_data = [
        [
            "RA-04 calculation",
            "Amount",
        ],
        [
            "Gross value",
            money(3883500),
        ],
        [
            "GST — 18%",
            money(699030),
        ],
        [
            "Retention — 5%",
            money(194175),
        ],
        [
            "Mobilisation advance",
            money(1043200),
        ],
        [
            "Previous recovery",
            money(718550),
        ],
        [
            "RA-04 advance recovery",
            money(324650),
        ],
        [
            "Net payable",
            money(4063705),
        ],
    ]

    story.append(
        make_table(
            totals_data,
            [
                85 * mm,
                75 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        info_box(
            "Billing control",
            "Disputed quantities are excluded from billing. "
            "QC-failed quantities are not billable. B05's "
            "250 m above the contract quantity is recorded as "
            "a variation rather than silently billed at the "
            "contract rate.",
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 4 — CASHFLOW
    # ========================================================

    story.append(
        section_header(
            "4",
            "Cash-flow Forecast",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "The forecast uses remaining BOQ quantities, "
            "the controlled schedule forecast and the stated "
            "billing/payment timing.",
        )
    )

    cash_data = [
        [
            "BOQ",
            "Remaining",
            "Finish",
            "Gross",
            "Payment",
        ],
        [
            "B02",
            "1,600 m",
            "Oct 2026",
            money(1840000),
            "05 Dec 2026",
        ],
        [
            "B03",
            "30 nos",
            "Oct 2026",
            money(1155000),
            "05 Dec 2026",
        ],
        [
            "B04",
            "8.9 km",
            "Oct 2026",
            money(1646500),
            "05 Dec 2026",
        ],
        [
            "B05",
            "700 m",
            "Oct 2026",
            money(154000),
            "05 Dec 2026",
        ],
        [
            "B06",
            "42 nos",
            "Oct 2026",
            money(609000),
            "05 Dec 2026",
        ],
        [
            "B07",
            "1 LS",
            "Nov 2026",
            money(450000),
            "04 Jan 2027",
        ],
    ]

    story.append(
        make_table(
            cash_data,
            [
                20 * mm,
                27 * mm,
                27 * mm,
                42 * mm,
                44 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    monthly_data = [
        [
            "Month",
            "Forecast cash inflow",
        ],
        [
            "October 2026",
            money(2385500),
        ],
        [
            "November 2026",
            money(4063705),
        ],
        [
            "December 2026",
            money(6107085),
        ],
    ]

    story.append(
        make_table(
            monthly_data,
            [
                75 * mm,
                85 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        info_box(
            "Forecast control",
            "Retention release is outside the forecast. "
            "No future mobilisation advance recovery is assumed "
            "in the forecast.",
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 5 — CONTROLS
    # ========================================================

    story.append(
        section_header(
            "5",
            "Project Controls & Exceptions",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    controls_data = [
        [
            "Control",
            "Result / Evidence",
        ],
        [
            "Traceability",
            "WBS → execution record → BOQ mapping supported.",
        ],
        [
            "Disputed quantity",
            "Measured, certified and disputed quantities are separated.",
        ],
        [
            "QC exclusion",
            "QC-failed fabrication is excluded from billable quantity.",
        ],
        [
            "Certification",
            "Certification requires an inspection certificate.",
        ],
        [
            "Invalid WBS",
            "Invalid WBS activity is flagged and never remapped.",
        ],
        [
            "Capacity",
            "EX-908 at 4,200 m exceeds the 800 m/day maximum and is flagged.",
        ],
        [
            "B04 variance",
            "8.98 km logged vs 5.2 km measured; no invented explanation.",
        ],
        [
            "B05 variation",
            "250 m certified above contract quantity recorded as variation.",
        ],
        [
            "Approval escalation",
            "PR-104 and PR-108 escalate because assigned approver is unavailable.",
        ],
        [
            "Anti-splitting",
            "PR-105 and PR-106 trigger aggregation rule.",
        ],
    ]

    story.append(
        make_table(
            controls_data,
            [
                43 * mm,
                117 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        paragraph(
            "Approval routing",
            "HeroCustom",
        )
    )

    approvals_data = [
        [
            "Request",
            "Routed approver",
        ],
        [
            "PR-101",
            "Arjun",
        ],
        [
            "PR-102",
            "Arjun",
        ],
        [
            "PR-103",
            "Neha",
        ],
        [
            "PR-104",
            "Vikram — escalation due to Neha leave",
        ],
        [
            "PR-105",
            "Vikram",
        ],
        [
            "PR-106",
            "Vikram — aggregate value rule",
        ],
        [
            "PR-107",
            "Suresh",
        ],
        [
            "PR-108",
            "Vikram — escalation due to unavailable approver",
        ],
        [
            "PR-109",
            "Neha",
        ],
    ]

    story.append(
        make_table(
            approvals_data,
            [
                45 * mm,
                115 * mm,
            ],
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 6 — AI
    # ========================================================

    story.append(
        section_header(
            "6",
            "AI Evaluation",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "Local Ollama execution-log extraction",
            "HeroCustom",
        )
    )

    story.append(
        paragraph(
            "All 26 execution remarks were processed using local "
            "Ollama. The hand-labelled reference set was compared "
            "field-by-field with the model output.",
        )
    )

    ai_data = [
        [
            "Field",
            "Correct",
            "Total",
            "Accuracy",
        ],
        [
            "Delay category",
            "24",
            "26",
            "92.31%",
        ],
        [
            "Delay hours",
            "26",
            "26",
            "100.00%",
        ],
    ]

    story.append(
        make_table(
            ai_data,
            [
                60 * mm,
                30 * mm,
                30 * mm,
                40 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        info_box(
            "Observed model errors",
            "EX-915 was classified as none instead of inspection; "
            "EX-925 was classified as labour instead of none.",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        rich_paragraph(
            "<b>Control:</b> The extraction prompt prohibits "
            "inventing delay hours. Unstated values remain "
            '"not stated".',
        )
    )

    story.append(
        paragraph(
            "ClickUp AI head-to-head verification",
            "HeroCustom",
        )
    )

    clickup_ai_data = [
        [
            "Test",
            "Result",
        ],
        [
            "Required project questions",
            "6 / 6 correct",
        ],
        [
            "Numeric questions included",
            "At least 4",
        ],
        [
            "Contract value",
            "INR 13,040,000 — verified",
        ],
        [
            "RA-04 totals",
            "Verified against deterministic calculation",
        ],
        [
            "Cashflow Oct/Nov/Dec",
            "Verified against deterministic forecast",
        ],
        [
            "B02 quantity/rate",
            "1,500 m / INR 1,150 — verified",
        ],
        [
            "B04 measured/certified/disputed",
            "5.2 / 4.9 / 0.3 km — verified",
        ],
    ]

    story.append(
        make_table(
            clickup_ai_data,
            [
                70 * mm,
                90 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        info_box(
            "ClickUp AI observation",
            "Global Brain indexing was less reliable for finding "
            "some project records, while task-level Brain queries "
            "returned the required answers correctly.",
            color=AMBER,
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 7 — FEASIBILITY
    # ========================================================

    story.append(
        section_header(
            "7",
            "F1–F13 Feasibility Verdicts",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "The feasibility assessment uses the four required "
            "buckets: NATIVE, CONFIGURATION, CUSTOM BUILD and "
            "NOT POSSIBLE.",
        )
    )

    verdict_data = [
        [
            "Requirement",
            "Verdict",
        ],
        [
            "F1 — Traceability",
            "CUSTOM BUILD",
        ],
        [
            "F2 — Certified / disputed separation",
            "CUSTOM BUILD",
        ],
        [
            "F3 — Monthly progress + milestone billing",
            "CUSTOM BUILD",
        ],
        [
            "F4 — Finance notification",
            "CUSTOM BUILD",
        ],
        [
            "F5 — Purchase approval limits",
            "CUSTOM BUILD",
        ],
        [
            "F6 — Approval rerouting",
            "CUSTOM BUILD",
        ],
        [
            "F7 — Certification control",
            "CUSTOM BUILD",
        ],
        [
            "F8 — WBS-based forecast",
            "CUSTOM BUILD",
        ],
        [
            "F9 — P6 / Microsoft Project import",
            "CUSTOM BUILD",
        ],
        [
            "F10 — SMS alerts",
            "CONFIGURATION",
        ],
        [
            "F11 — Private-network hosting",
            "NOT POSSIBLE",
        ],
        [
            "F12 — Full Excel export",
            "CONFIGURATION",
        ],
        [
            "F13 — AI management reports",
            "CUSTOM BUILD",
        ],
    ]

    story.append(
        make_table(
            verdict_data,
            [
                100 * mm,
                60 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    counts_data = [
        [
            "Bucket",
            "Count",
        ],
        [
            "NATIVE",
            "0",
        ],
        [
            "CONFIGURATION",
            "2",
        ],
        [
            "CUSTOM BUILD",
            "10",
        ],
        [
            "NOT POSSIBLE",
            "1",
        ],
    ]

    story.append(
        make_table(
            counts_data,
            [
                100 * mm,
                60 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        info_box(
            "Key feasibility finding",
            "F11 is classified as NOT POSSIBLE because ClickUp "
            "is a SaaS platform hosted on ClickUp's infrastructure "
            "rather than being deployable entirely inside the "
            "client's private network.",
            color=RED,
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        paragraph(
            "For non-NATIVE requirements, the feasibility document "
            "records the required workaround or build approach, "
            "limitations and client-facing expectation.",
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 8 — FINAL VERIFICATION
    # ========================================================

    story.append(
        section_header(
            "8",
            "Data Handling & Final Verification",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "Data handling",
            "HeroCustom",
        )
    )

    data_controls = [
        "Contract values and project rates remain inside "
        "the controlled project environment.",
        "Local Ollama is accessed through 127.0.0.1:11434.",
        "No external AI service is used for deterministic " "project calculations.",
        "AI narrative receives already-computed report values "
        "and is instructed not to alter or invent numbers.",
        "Secrets are excluded from Git through .gitignore.",
        "Generated artifacts and local data are excluded " "where required.",
    ]

    for item in data_controls:
        story.append(bullet(item))

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    verification_data = [
        [
            "Verification",
            "Result",
        ],
        [
            "Automated tests",
            "22 / 22 passed",
        ],
        [
            "Git working tree check",
            "git diff --check clean",
        ],
        [
            "XER importer",
            "Idempotent",
        ],
        [
            "RA-04 calculation",
            "Verified",
        ],
        [
            "Cashflow forecast",
            "Verified",
        ],
        [
            "Purchase approval router",
            "Verified",
        ],
        [
            "Local Ollama",
            "26 / 26 remarks processed",
        ],
        [
            "Local Ollama category accuracy",
            "92.31%",
        ],
        [
            "Local Ollama hours accuracy",
            "100%",
        ],
        [
            "ClickUp AI",
            "6 / 6 required questions correct",
        ],
        [
            "Evidence screenshots",
            "12 / 12",
        ],
        [
            "Repository",
            "Public GitHub repository",
        ],
    ]

    story.append(
        make_table(
            verification_data,
            [
                85 * mm,
                75 * mm,
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        info_box(
            "Submission checklist",
            "The PDF covers the dated build evidence, feasibility "
            "verdicts, AI accuracy, RA-04 bill, cashflow forecast "
            "and all 12 evidence screenshots. The remaining "
            "submission actions are the 10-minute voice-and-screen "
            "demonstration and the required ClickUp guest invitation "
            "to rajesh@delipat.com.",
        )
    )

    story.append(PageBreak())

    # ========================================================
    # SECTION 9 — SCREENSHOTS
    # ========================================================

    story.append(
        section_header(
            "9",
            "Evidence Screenshots",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        paragraph(
            "The following 12 evidence items document the "
            "implementation, ClickUp configuration, calculations, "
            "AI evaluation, testing, repository and feasibility "
            "assessment.",
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    for (
        number,
        title,
        filename,
    ) in SCREENSHOT_FILES:

        add_evidence(
            story,
            number,
            title,
            filename,
        )

    return story


# ============================================================
# DOCUMENT TEMPLATES
# ============================================================


"""
Configures the PDF document and page templates so the assembled report can be rendered consistently.
"""


def build_document():

    document = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=("Delipat Assignment 3 — " "Final Submission"),
        author="Kaveri Infrasystems",
        subject=("Delipat IT Assignment 3 " "Live Implementation"),
    )

    # --------------------------------------------------------
    # Portrait frame
    # --------------------------------------------------------

    portrait_frame = Frame(
        17 * mm,
        18 * mm,
        A4[0] - 34 * mm,
        A4[1] - 36 * mm,
        id="portrait_frame",
    )

    # --------------------------------------------------------
    # Landscape evidence frame
    # --------------------------------------------------------

    landscape_width, landscape_height = LANDSCAPE

    landscape_frame = Frame(
        14 * mm,
        14 * mm,
        landscape_width - 28 * mm,
        landscape_height - 28 * mm,
        id="landscape_frame",
    )

    # --------------------------------------------------------
    # Portrait evidence frame
    # --------------------------------------------------------

    portrait_evidence_frame = Frame(
        17 * mm,
        18 * mm,
        A4[0] - 34 * mm,
        A4[1] - 36 * mm,
        id="portrait_evidence_frame",
    )

    # --------------------------------------------------------
    # Page templates
    # --------------------------------------------------------

    document.addPageTemplates(
        [
            PageTemplate(
                id="portrait",
                frames=[portrait_frame],
                pagesize=A4,
                onPage=portrait_page,
            ),
            PageTemplate(
                id="evidence_landscape",
                frames=[landscape_frame],
                pagesize=LANDSCAPE,
                onPage=landscape_page,
            ),
            PageTemplate(
                id="evidence_portrait",
                frames=[portrait_evidence_frame],
                pagesize=A4,
                onPage=portrait_page,
            ),
        ]
    )

    return document


# ============================================================
# GENERATE PDF
# ============================================================


"""
Checks inputs and generates the final PDF through one clear command-line entry point.
"""


def main():

    validate_inputs()

    FINAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = build_document()

    document.build(build_story())

    print()
    print("=" * 64)
    print("PDF GENERATION COMPLETE")
    print("=" * 64)

    print(
        "Output:",
        OUTPUT,
    )

    print(
        "Size:",
        f"{OUTPUT.stat().st_size:,}",
        "bytes",
    )

    print("=" * 64)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
