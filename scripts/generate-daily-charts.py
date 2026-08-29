from pathlib import Path
from datetime import date, timedelta
import re

ROOT = Path(__file__).resolve().parents[1]

CHARTS = ROOT / "charts"
GDL_TEMPLATE = ROOT / "gdl-template.html"
MTP_TEMPLATE = ROOT / "mtp-template.html"
INDEX = ROOT / "index.html"

SITE = "https://www.cartalotto.com"

# GDL Perdana = EVERY DAY
GDL_WEEKDAYS = {0, 1, 2, 3, 4, 5, 6}

# Ramalan 4D MTP & SGP = Wednesday, Saturday, Sunday
MTP_WEEKDAYS = {2, 5, 6}

# Today + 14 future days
FUTURE_DAYS = 14


def long_date(d):
    return d.strftime("%B %-d, %Y")


def display_date(d):
    return d.strftime("%d/%m/%Y")


def iso_date(d):
    return d.strftime("%Y-%m-%d")


def make_matrix(active_positions):
    values = [
        "8", "1", "6", "4",
        "3", "7", "0", "9",
        "5", "2", "8", "1",
        "6", "4", "3", "7"
    ]

    html = []

    for i, value in enumerate(values):
        cls = "cell active" if i in active_positions else "cell"
        html.append(f'<div class="{cls}">{value}</div>')

    return "\n".join(html)


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


def write_page(filename, html):
    path = CHARTS / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def existing_dates(prefix):
    pattern = re.compile(
        rf"^{re.escape(prefix)}-(\d{{4}}-\d{{2}}-\d{{2}})\.html$"
    )

    result = []

    if not CHARTS.exists():
        return result

    for file in CHARTS.glob("*.html"):
        match = pattern.match(file.name)

        if match:
            try:
                year, month, day = map(int, match.group(1).split("-"))
                result.append(date(year, month, day))
            except ValueError:
                pass

    return sorted(set(result))


def generate_gdl(start):

    template = GDL_TEMPLATE.read_text(encoding="utf-8")

    dates = [
        start + timedelta(days=offset)
        for offset in range(FUTURE_DAYS + 1)
        if (start + timedelta(days=offset)).weekday() in GDL_WEEKDAYS
    ]

    # Include old pages so Previous links remain valid.
    all_dates = sorted(set(existing_dates("carta-ramalan-gdl-perdana") + dates))

    for d in dates:

        index = all_dates.index(d)

        previous_date = all_dates[index - 1] if index > 0 else None
        next_date = all_dates[index + 1] if index + 1 < len(all_dates) else None

        filename = f"carta-ramalan-gdl-perdana-{iso_date(d)}.html"

        previous_url = (
            f"{SITE}/charts/carta-ramalan-gdl-perdana-{iso_date(previous_date)}"
            if previous_date else SITE
        )

        next_url = (
            f"{SITE}/charts/carta-ramalan-gdl-perdana-{iso_date(next_date)}"
            if next_date else SITE
        )

        title = f"Carta Ramalan GDL Perdana — {long_date(d)}"

        matrix = make_matrix({0, 5, 10, 13})

        html = render(
            template,
            title,
            d,
            matrix,
            next_url,
            previous_url
        )

        write_page(filename, html)


def generate_mtp(start):

    template = MTP_TEMPLATE.read_text(encoding="utf-8")

    dates = [
        start + timedelta(days=offset)
        for offset in range(FUTURE_DAYS + 1)
        if (start + timedelta(days=offset)).weekday() in MTP_WEEKDAYS
    ]

    # Include old pages so Previous links remain valid.
    all_dates = sorted(set(existing_dates("ramalan-4d-mtp-sgp") + dates))

    for d in dates:

        index = all_dates.index(d)

        previous_date = all_dates[index - 1] if index > 0 else None
        next_date = all_dates[index + 1] if index + 1 < len(all_dates) else None

        filename = f"ramalan-4d-mtp-sgp-{iso_date(d)}.html"

        previous_url = (
            f"{SITE}/charts/ramalan-4d-mtp-sgp-{iso_date(previous_date)}"
            if previous_date else SITE
        )

        next_url = (
            f"{SITE}/charts/ramalan-4d-mtp-sgp-{iso_date(next_date)}"
            if next_date else SITE
        )

        title = f"Ramalan 4D MTP & SGP — {long_date(d)}"

        matrix = make_matrix({0, 3, 5, 10})

        html = render(
            template,
            title,
            d,
            matrix,
            next_url,
            previous_url
        )

        write_page(filename, html)


def latest_existing_date(prefix, allowed_days, today):

    dates = existing_dates(prefix)

    valid = [
        d for d in dates
        if d <= today and d.weekday() in allowed_days
    ]

    if valid:
        return max(valid)

    return None


def update_index(today):

    if not INDEX.exists():
        return

    html = INDEX.read_text(encoding="utf-8")

    # Latest GDL
    gdl_date = latest_existing_date(
        "carta-ramalan-gdl-perdana",
        GDL_WEEKDAYS,
        today
    )

    # Latest MTP/SGP
    mtp_date = latest_existing_date(
        "ramalan-4d-mtp-sgp",
        MTP_WEEKDAYS,
        today
    )

    if gdl_date:
        gdl_url = (
            f"/charts/carta-ramalan-gdl-perdana-{iso_date(gdl_date)}"
        )

        html = re.sub(
            r'href="/charts/carta-ramalan-gdl-perdana-\d{4}-\d{2}-\d{2}"',
            f'href="{gdl_url}"',
            html,
            count=1
        )

    if mtp_date:
        mtp_url = (
            f"/charts/ramalan-4d-mtp-sgp-{iso_date(mtp_date)}"
        )

        html = re.sub(
            r'href="/charts/ramalan-4d-mtp-sgp-\d{4}-\d{2}-\d{2}"',
            f'href="{mtp_url}"',
            html,
            count=1
        )

    INDEX.write_text(html, encoding="utf-8")


def main():

    CHARTS.mkdir(parents=True, exist_ok=True)

    today = date.today()

    # IMPORTANT:
    # Do NOT delete old chart pages.
    generate_gdl(today)
    generate_mtp(today)

    update_index(today)

    print("Carta Lotto daily chart system completed.")
    print(f"Today: {today}")
    print(f"Future days generated: {FUTURE_DAYS}")
    print("Old dated pages preserved.")
    print("Homepage latest links updated.")


if __name__ == "__main__":
    main()
