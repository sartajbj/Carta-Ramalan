from pathlib import Path
from datetime import date
import re
from html import escape

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
GDL_TEMPLATE = ROOT / "gdl-template.html"
MTP_TEMPLATE = ROOT / "mtp-template.html"
INDEX = ROOT / "index.html"

SITE = "https://www.cartalotto.com"

# Publication schedule
GDL_WEEKDAYS = {0, 1, 2, 3, 4, 5, 6}
MTP_WEEKDAYS = {2, 5, 6}  # Wednesday, Saturday, Sunday

# IMPORTANT:
# This generator deliberately creates TODAY only.
# It never creates future dated pages.
GENERATE_FUTURE_DAYS = False

# IMPORTANT:
# These values are the current chart-layout data already used by the project.
# They are NOT official lottery results. Do not describe them as official results.
#
# Replace this data only when you have the real/published chart information.
MTP_VALUES = [
    "8", "1", "6", "4",
    "3", "7", "0", "9",
    "5", "2", "8", "1",
    "6", "4", "3", "7"
]
MTP_ACTIVE = {0, 3, 5, 10}


def long_date(d):
    return d.strftime("%B %d, %Y").replace(" 0", " ")


def display_date(d):
    return d.strftime("%d/%m/%Y")


def iso_date(d):
    return d.strftime("%Y-%m-%d")


def slug_for(d):
    return f"ramalan-4d-mtp-sgp-{iso_date(d)}.html"


def url_for(d):
    return f"{SITE}/charts/{slug_for(d)}"


def existing_dates(prefix):
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d{{4}}-\d{{2}}-\d{{2}})\.html$")
    result = []

    if not CHARTS.exists():
        return result

    for path in CHARTS.glob("*.html"):
        match = pattern.match(path.name)
        if not match:
            continue
        try:
            y, m, d = map(int, match.group(1).split("-"))
            result.append(date(y, m, d))
        except ValueError:
            pass

    return sorted(set(result))


def make_matrix(values, active_positions):
    if len(values) != 16:
        raise ValueError("MTP chart must contain exactly 16 positions.")

    cells = []
    for i, value in enumerate(values):
        cls = "cell active" if i in active_positions else "cell"
        cells.append(f'<div class="{cls}">{escape(str(value))}</div>')
    return "\n".join(cells)


def nav_link(url, label):
    return f'<a class="btn" href="{escape(url, quote=True)}">{escape(label)}</a>'


def find_previous_next(d, dates):
    older = [x for x in dates if x < d]
    newer = [x for x in dates if x > d]
    previous_date = max(older) if older else None
    next_date = min(newer) if newer else None
    return previous_date, next_date


def build_page(d, template, all_dates):
    previous_date, next_date = find_previous_next(d, all_dates)

    # Do not create links to files that do not exist.
    previous_link = (
        nav_link(url_for(previous_date), f"← Previous Chart · {display_date(previous_date)}")
        if previous_date else ""
    )
    next_link = (
        nav_link(url_for(next_date), f"Next Chart · {display_date(next_date)} →")
        if next_date else ""
    )

    title = f"Ramalan 4D MTP & SGP — {long_date(d)}"
    description = (
        f"Ramalan 4D MTP & SGP chart for {long_date(d)}. "
        "View the dated 4 × 4 chart layout and use the existing archive links "
        "to browse previous and next MTP/SGP chart pages."
    )

    lead = (
        f"This dated Ramalan 4D MTP & SGP page presents the 4 × 4 chart layout "
        f"for {long_date(d)}. Check the date and category before using the chart, "
        "and remember that the highlighted positions are layout markers, not official results."
    )

    heading_1 = f"Ramalan 4D MTP & SGP Chart for {long_date(d)}"
    paragraph_1 = (
        f"The chart above is organized for the {display_date(d)} MTP & SGP date. "
        "All sixteen positions are displayed so the complete 4 × 4 layout can be read without opening another view."
    )
    paragraph_2 = (
        "Highlighted cells identify positions that are visually marked in this chart layout. "
        "They do not represent an official draw result, a guaranteed number, or a promise of winnings."
    )

    heading_2 = "Reading This 4D Chart"
    paragraph_3 = (
        "Start with the category and date, then read the grid from left to right and top to bottom. "
        "When comparing dates, use the archive navigation rather than assuming that one page contains the next update."
    )
    paragraph_4 = (
        "Carta Lotto keeps dated pages separate so an older archive entry remains tied to its own date. "
        "For official draw results, use the relevant official lottery source instead of treating this chart as an official results page."
    )

    replacements = {
        "{{TITLE}}": escape(title),
        "{{DESCRIPTION}}": escape(description, quote=True),
        "{{SLUG}}": slug_for(d),
        "{{DATE}}": iso_date(d),
        "{{DATE_TEXT}}": escape(long_date(d)),
        "{{DATE_SHORT}}": escape(display_date(d)),
        "{{LEAD}}": escape(lead),
        "{{MATRIX}}": make_matrix(MTP_VALUES, MTP_ACTIVE),
        "{{HEADING_1}}": escape(heading_1),
        "{{PARAGRAPH_1}}": escape(paragraph_1),
        "{{PARAGRAPH_2}}": escape(paragraph_2),
        "{{HEADING_2}}": escape(heading_2),
        "{{PARAGRAPH_3}}": escape(paragraph_3),
        "{{PARAGRAPH_4}}": escape(paragraph_4),
        "{{PREVIOUS_LINK}}": previous_link,
        "{{NEXT_LINK}}": next_link,
        "{{GDL_URL}}": f"{SITE}/charts/carta-ramalan-gdl-perdana-{iso_date(latest_gdl_date(d))}.html",
    }

    content = template
    for key, value in replacements.items():
        content = content.replace(key, value)

    # Fail closed: no unresolved generator tokens may reach production.
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", content)))
    if unresolved:
        raise RuntimeError(f"Unresolved template placeholders: {unresolved}")

    return content


def latest_gdl_date(today):
    dates = [d for d in existing_dates("carta-ramalan-gdl-perdana") if d <= today]
    if not dates:
        raise RuntimeError(
            "No existing GDL dated page was found. MTP page generation stopped "
            "so the GDL navigation cannot point to a non-existing file."
        )
    return max(dates)


def generate_mtp(today):
    if today.weekday() not in MTP_WEEKDAYS:
        print(f"No MTP/SGP page generated: {today} is not a scheduled MTP/SGP day.")
        return

    template = MTP_TEMPLATE.read_text(encoding="utf-8")

    existing = existing_dates("ramalan-4d-mtp-sgp")
    all_dates = sorted(set(existing + [today]))

    filename = slug_for(today)
    html = build_page(today, template, all_dates)

    path = CHARTS / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")

    print(f"Generated: {path}")


def update_existing_mtp_navigation():
    """
    Rebuild navigation links for existing MTP pages without creating future pages.
    This fixes old pages that previously pointed to URLs without .html.
    """
    dates = existing_dates("ramalan-4d-mtp-sgp")
    if not dates:
        return

    template = MTP_TEMPLATE.read_text(encoding="utf-8")

    for d in dates:
        path = CHARTS / slug_for(d)
        if not path.exists():
            continue

        # Existing page may contain old placeholder-free content, so navigation
        # is repaired directly rather than regenerating old editorial content.
        html = path.read_text(encoding="utf-8")

        previous_date, next_date = find_previous_next(d, dates)
        previous_html = (
            nav_link(url_for(previous_date), f"← Previous Chart · {display_date(previous_date)}")
            if previous_date else ""
        )
        next_html = (
            nav_link(url_for(next_date), f"Next Chart · {display_date(next_date)} →")
            if next_date else ""
        )

        # Replace only the old navigation block if it is identifiable.
        pattern = re.compile(
            r'<div class="actions">.*?</div>',
            re.DOTALL
        )
        replacement = (
            '<div class="actions">'
            '<a class="btn primary" href="/">← Home</a>'
            f'{previous_html}{next_html}'
            f'<a class="btn" href="{SITE}/charts/carta-ramalan-gdl-perdana-{iso_date(latest_gdl_date(d))}.html">Latest GDL Perdana</a>'
            '</div>'
        )

        new_html, count = pattern.subn(replacement, html, count=1)
        if count:
            path.write_text(new_html, encoding="utf-8")


def main():
    CHARTS.mkdir(parents=True, exist_ok=True)
    today = date.today()

    generate_mtp(today)
    update_existing_mtp_navigation()

    print("Carta Lotto MTP/SGP generator completed.")
    print(f"Today: {today}")
    print("MTP/SGP schedule: Wednesday, Saturday, Sunday")
    print("Future pages: DISABLED")
    print("Navigation: existing-file-only, .html URLs")
    print("Unresolved template tokens: blocked")


if __name__ == "__main__":
    main()
