from pathlib import Path
from datetime import date, timedelta
import re

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
GDL_TEMPLATE = ROOT / "gdl-template.html"
MTP_TEMPLATE = ROOT / "mtp-template.html"

# -----------------------------
# SETTINGS
# -----------------------------

SITE = "https://www.cartalotto.com"

# GDL Perdana chart days
GDL_WEEKDAYS = {0, 2, 5}  # Monday, Wednesday, Saturday

# MTP / SGP chart days
MTP_WEEKDAYS = {0, 1, 2, 3, 4, 5, 6}  # Daily

# How many future dated pages to generate
FUTURE_DAYS = 14

# -----------------------------
# HELPERS
# -----------------------------

def long_date(d):
    return d.strftime("%B %-d, %Y") if Path("/").exists() else d.strftime("%B %d, %Y")


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
    content = template

    replacements = {
        "{{TITLE}}": title,
        "{{DATE}}": iso_date(d),
        "{{DATE_LONG}}": long_date(d),
        "{{DATE_DISPLAY}}": display_date(d),
        "{{MATRIX}}": matrix,
        "{{NEXT_URL}}": next_url,
        "{{PREVIOUS_URL}}": previous_url,
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    return content


def write_page(filename, html):
    path = CHARTS / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


# -----------------------------
# REMOVE OLD GENERATED DAILY
# PAGES ONLY
# -----------------------------

def clean_generated_pages(prefix):
    pattern = re.compile(
        rf"^{re.escape(prefix)}-\d{{4}}-\d{{2}}-\d{{2}}\.html$"
    )

    for file in CHARTS.glob("*.html"):
        if pattern.match(file.name):
            file.unlink()


# -----------------------------
# GENERATE GDL
# -----------------------------

def generate_gdl(start):
    template = GDL_TEMPLATE.read_text(encoding="utf-8")

    dates = []

    for offset in range(FUTURE_DAYS + 1):
        d = start + timedelta(days=offset)

        if d.weekday() in GDL_WEEKDAYS:
            dates.append(d)

    for index, d in enumerate(dates):

        previous_date = dates[index - 1] if index > 0 else None
        next_date = dates[index + 1] if index + 1 < len(dates) else None

        filename = f"carta-ramalan-gdl-perdana-{iso_date(d)}.html"
        url = f"{SITE}/charts/{filename[:-5]}"

        previous_url = (
            f"{SITE}/charts/carta-ramalan-gdl-perdana-{iso_date(previous_date)}"
            if previous_date else SITE
        )

        next_url = (
            f"{SITE}/charts/carta-ramalan-gdl-perdana-{iso_date(next_date)}"
            if next_date else SITE
        )

        title = f"Carta Ramalan GDL Perdana — {long_date(d)}"

        # Fixed example layout.
        # Replace chart numbers later with the actual daily chart data.
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


# -----------------------------
# GENERATE MTP / SGP
# -----------------------------

def generate_mtp(start):
    template = MTP_TEMPLATE.read_text(encoding="utf-8")

    dates = []

    for offset in range(FUTURE_DAYS + 1):
        d = start + timedelta(days=offset)

        if d.weekday() in MTP_WEEKDAYS:
            dates.append(d)

    for index, d in enumerate(dates):

        previous_date = dates[index - 1] if index > 0 else None
        next_date = dates[index + 1] if index + 1 < len(dates) else None

        filename = f"ramalan-4d-mtp-sgp-{iso_date(d)}.html"
        url = f"{SITE}/charts/{filename[:-5]}"

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


# -----------------------------
# MAIN
# -----------------------------

def main():
    CHARTS.mkdir(parents=True, exist_ok=True)

    today = date.today()

    clean_generated_pages("carta-ramalan-gdl-perdana")
    clean_generated_pages("ramalan-4d-mtp-sgp")

    generate_gdl(today)
    generate_mtp(today)

    print("Daily Carta Lotto charts generated successfully.")
    print(f"Start date: {today}")
    print(f"Future days: {FUTURE_DAYS}")


if __name__ == "__main__":
    main()
