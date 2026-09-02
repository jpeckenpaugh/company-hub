"""Simple, clean one-page PDF summary generation via fpdf2.

The layout is an implementation detail. Text is rendered with a Unicode font
when one is available on the host so user data with non-latin-1 characters
never crashes generation; otherwise it falls back to a latin-1 core font with
sanitized text.
"""

from pathlib import Path

from fpdf import FPDF

UNICODE_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)


def _find_unicode_font() -> str | None:
    for path in UNICODE_FONT_CANDIDATES:
        if Path(path).is_file():
            return path
    return None


def _latin1_safe(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


def _setup_font(pdf: FPDF) -> tuple[str, bool]:
    font_path = _find_unicode_font()
    if font_path:
        pdf.add_font("Body", "", font_path)
        pdf.add_font("Body", "B", font_path)
        return "Body", True
    return "Helvetica", False


def generate_summary(company: dict) -> bytes:
    """Return the bytes of a one-page summary PDF for a company dict."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    font, unicode_ok = _setup_font(pdf)

    def t(text: str) -> str:
        return text if unicode_ok else _latin1_safe(text or "")

    pdf.set_font(font, "B", 20)
    pdf.cell(0, 12, t(company["name"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font(font, "B", 11)
    pdf.cell(0, 7, "Company Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
    pdf.ln(6)

    rows = [
        ("Industry", company.get("industry")),
        ("Headquarters", company.get("hq_location")),
        ("Website", company.get("website")),
        ("Contact Email", company.get("contact_email")),
        ("Contact Phone", company.get("contact_phone")),
        ("Description", company.get("description")),
    ]

    pdf.set_font(font, "", 11)
    for label, value in rows:
        pdf.set_font(font, "B", 11)
        pdf.cell(45, 7, t(label), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font, "", 11)
        pdf.multi_cell(0, 6, t(value or "—"))
        pdf.ln(1)

    pdf.ln(4)
    pdf.set_font(font, "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, t(f"Generated: {company.get('updated_at', '')}"),
             new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
