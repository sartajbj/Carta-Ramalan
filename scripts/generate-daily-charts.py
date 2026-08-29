from pathlib import Path
from datetime import date, timedelta
import re

ROOT = Path(__file__).resolve().parents[1]

CHARTS = ROOT / "charts"
GDL_TEMPLATE = ROOT / "gdl-template.html"
MTP_TEMPLATE = ROOT / "mtp-template.html"
INDEX = ROOT / "index.html"

SITE = "https://www.cartalotto.com"

# ============================================================
# SCHEDULE
# ============================================================

# GDL Perdana = EVERY DAY
GDL_WEEKDAYS = {0, 1, 2, 3, 4, 5, 6}

# Ramalan 4D MTP & SGP = Wednesday, Saturday, Sunday
MTP_WEEKDAYS = {2, 5, 6}

# Generate today + next 14 days
FUTURE_DAYS = 14


# ============================================================
# DATE HELPERS
# ============================================================

def long_date(d):
    return d.strftime("%B %d, %Y").replace(" 0", " ")


def display_date(d):
    return d.strftime("%d/%m/%Y")


def iso_date(d):
    return d.strftime("%Y-%m-%d")


# ============================================================
# CHART MATRIX
# ============================================================

def make_matrix(active_positions):

    values = [
        "8", "1", "6", "4",
        "3", "7", "0", "9",
        "5", "2", "8", "1",
        "6", "4", "3", "7"
    ]

    html = []

    for i, value in enumerate(values):

        if i in active_positions:
            cls = "cell active"
        else:
            cls = "cell"

        html.append(
            f'<div class="{cls}">{value}</div>'
        )

    return "\n".join(html)


# ============================================================
# TEMPLATE RENDER
# ============================================================

def render(template, title, d, matrix, next_url, previous_url):

    replacements = {
        "{{TITLE}}": title,
        "{{DATE}}": iso_date(d),
        "{{DATE_LONG}}": long_date(d),
        "{{DATE_DISPLAY}}": display_date(d),
        "{{MATRIX}}": matrix,
        "{{NEXT_URL}}": next_url,
        "{{PREVIOUS_URL}}": previous_url,
    }

    content = template

    for key, value in replacements.items():
        content = content.replace(key, value)

    return content


# ============================================================
# WRITE PAGE
# ============================================================

def write_page(filename, html):

    path = CHARTS / filename

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        html,
        encoding="utf-8"
    )


# ============================================================
# FIND EXISTING DATED PAGES
# ============================================================

def existing_dates(prefix):

    pattern = re.compile(
        rf"^{re.escape(prefix)}-(\d{{4}}-\d{{2}}-\d{{2}})\.html$"
    )

    result = []

    if not CHARTS.exists():
        return result

    for file in CHARTS.glob("*.html"):

        match = pattern.match(file.name)

        if not match:
            continue

        try:

            year, month, day = map(
                int,
                match.group(1).split("-")
            )

            result.append(
                date(year, month, day)
            )

        except ValueError:
            continue

    return sorted(set(result))


# ============================================================
# GENERATE DATE RANGE
# ============================================================

def future_dates(start, allowed_days):

    result = []

    for offset in range(FUTURE_DAYS + 1):

        d = start + timedelta(days=offset)

        if d.weekday() in allowed_days:
            result.append(d)

    return result


# ============================================================
# GDL PERDANA
# ============================================================

def generate_gdl(start):

    template = GDL_TEMPLATE.read_text(
        encoding="utf-8"
    )

    new_dates = future_dates(
        start,
        GDL_WEEKDAYS
    )

    old_dates = existing_dates(
        "carta-ramalan-gdl-perdana"
    )

    # IMPORTANT:
    # Old pages are NEVER deleted.
    all_dates = sorted(
        set(old_dates + new_dates)
    )

    for d in new_dates:

        index = all_dates.index(d)

        previous_date = (
            all_dates[index - 1]
            if index > 0
            else None
        )

        next_date = (
            all_dates[index + 1]
            if index + 1 < len(all_dates)
            else None
        )

        filename = (
            f"carta-ramalan-gdl-perdana-"
            f"{iso_date(d)}.html"
        )

        previous_url = (
            f"{SITE}/charts/"
            f"carta-ramalan-gdl-perdana-"
            f"{iso_date(previous_date)}"
            if previous_date
            else SITE
        )

        next_url = (
            f"{SITE}/charts/"
            f"carta-ramalan-gdl-perdana-"
            f"{iso_date(next_date)}"
            if next_date
            else SITE
        )

        title = (
            f"Carta Ramalan GDL Perdana — "
            f"{long_date(d)}"
        )

        matrix = make_matrix({
            0, 5, 10, 13
        })

        html = render(
            template,
            title,
            d,
            matrix,
            next_url,
            previous_url
        )

        write_page(
            filename,
            html
        )


# ============================================================
# MTP / SGP
# ============================================================

def generate_mtp(start):

    template = MTP_TEMPLATE.read_text(
        encoding="utf-8"
    )

    new_dates = future_dates(
        start,
        MTP_WEEKDAYS
    )

    old_dates = existing_dates(
        "ramalan-4d-mtp-sgp"
    )

    # IMPORTANT:
    # Old pages are NEVER deleted.
    all_dates = sorted(
        set(old_dates + new_dates)
    )

    for d in new_dates:

        index = all_dates.index(d)

        previous_date = (
            all_dates[index - 1]
            if index > 0
            else None
        )

        next_date = (
            all_dates[index + 1]
            if index + 1 < len(all_dates)
            else None
        )

        filename = (
            f"ramalan-4d-mtp-sgp-"
            f"{iso_date(d)}.html"
        )

        previous_url = (
            f"{SITE}/charts/"
            f"ramalan-4d-mtp-sgp-"
            f"{iso_date(previous_date)}"
            if previous_date
            else SITE
        )

        next_url = (
            f"{SITE}/charts/"
            f"ramalan-4d-mtp-sgp-"
            f"{iso_date(next_date)}"
            if next_date
            else SITE
        )

        title = (
            f"Ramalan 4D MTP & SGP — "
            f"{long_date(d)}"
        )

        matrix = make_matrix({
            0, 3, 5, 10
        })

        html = render(
            template,
            title,
            d,
            matrix,
            next_url,
            previous_url
        )

        write_page(
            filename,
            html
        )


# ============================================================
# LATEST VALID DATE
# ============================================================

def latest_existing_date(
    prefix,
    allowed_days,
    today
):

    dates = existing_dates(prefix)

    valid = [
        d
        for d in dates
        if d <= today
        and d.weekday() in allowed_days
    ]

    if not valid:
        return None

    return max(valid)


# ============================================================
# UPDATE HOMEPAGE LINKS
# ============================================================

def update_index(today):

    if not INDEX.exists():
        return

    html = INDEX.read_text(
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Latest GDL
    # --------------------------------------------------------

    gdl_date = latest_existing_date(
        "carta-ramalan-gdl-perdana",
        GDL_WEEKDAYS,
        today
    )

    if gdl_date:

        gdl_url = (
            f"/charts/"
            f"carta-ramalan-gdl-perdana-"
            f"{iso_date(gdl_date)}"
        )

        html = re.sub(
            r'href="/charts/'
            r'carta-ramalan-gdl-perdana-'
            r'\d{4}-\d{2}-\d{2}"',

            f'href="{gdl_url}"',

            html
        )

    # --------------------------------------------------------
    # Latest MTP / SGP
    # --------------------------------------------------------

    mtp_date = latest_existing_date(
        "ramalan-4d-mtp-sgp",
        MTP_WEEKDAYS,
        today
    )

    if mtp_date:

        mtp_url = (
            f"/charts/"
            f"ramalan-4d-mtp-sgp-"
            f"{iso_date(mtp_date)}"
        )

        html = re.sub(
            r'href="/charts/'
            r'ramalan-4d-mtp-sgp-'
            r'\d{4}-\d{2}-\d{2}"',

            f'href="{mtp_url}"',

            html
        )

    INDEX.write_text(
        html,
        encoding="utf-8"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    CHARTS.mkdir(
        parents=True,
        exist_ok=True
    )

    today = date.today()

    # Generate GDL daily pages.
    generate_gdl(today)

    # Generate MTP only Wed/Sat/Sun.
    generate_mtp(today)

    # Update homepage latest links.
    update_index(today)

    print(
        "========================================"
    )
    print(
        "Carta Lotto daily system completed."
    )
    print(
        f"Today: {today}"
    )
    print(
        f"Future days: {FUTURE_DAYS}"
    )
    print(
        "GDL: Daily"
    )
    print(
        "MTP/SGP: Wednesday, Saturday, Sunday"
    )
    print(
        "Old dated pages: PRESERVED"
    )
    print(
        "Homepage links: UPDATED"
    )
    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
