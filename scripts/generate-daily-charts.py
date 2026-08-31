"""
generate-daily-charts.py

Does two things, in order:

1. CREATE — if today's (Malaysia/Singapore time, UTC+8) GDL Perdana
   page doesn't exist yet, create it. If today is Wednesday,
   Saturday or Sunday and today's MTP/SGP page doesn't exist yet,
   create it too. Both use the real deterministic chart algorithm
   (ported 1:1 from the site's JavaScript -- verified to produce
   identical numbers) so the homepage preview and the full post
   always show the same chart for the same date.

   This step is idempotent: if a file for today already exists,
   nothing is overwritten and nothing is duplicated. No future
   dates are ever created.

2. MAINTAIN — (unchanged from before) repairs canonical URLs,
   og:url, and Previous/Home/Next navigation across every existing
   archive page, based on the real files present on disk. This
   runs after creation so a newly created page is correctly wired
   into its neighbours' navigation too.

Run:  python scripts/generate-daily-charts.py
"""

from pathlib import Path
from datetime import date, datetime, timedelta, timezone
import math
import re

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
TEMPLATES = ROOT / "templates"

SITE = "https://www.cartalotto.com"

GDL_PREFIX = "carta-ramalan-gdl-perdana"
MTP_PREFIX = "ramalan-4d-mtp-sgp"

GDL_TEMPLATE = TEMPLATES / "gdl-template.html"
MTP_TEMPLATE = TEMPLATES / "mtp-template.html"

MYT = timezone(timedelta(hours=8))


# ==========================================================
# TIME
# ==========================================================

def today_myt():
    """Today's date in Malaysia/Singapore time (UTC+8, no DST)."""
    return datetime.now(timezone.utc).astimezone(MYT).date()


def is_mtp_day(d):
    """Wednesday, Saturday, Sunday. Python weekday(): Mon=0..Sun=6."""
    return d.weekday() in (2, 5, 6)


def format_long(d):
    return f"{d.strftime('%B')} {d.day}, {d.year}"


# ==========================================================
# DETERMINISTIC CHART ALGORITHM
# (must stay byte-for-byte identical to the homepage JS version)
# ==========================================================

def seeded_random(seed):
    x = math.sin(seed) * 10000
    return x - math.floor(x)


def chart_index(y, m, d, type_):
    base = y + m * 31 + d * 17
    return base + 701 if type_ == "mtp" else base + 301


def generate_matrix(y, m, d, type_):
    seed = chart_index(y, m, d, type_)
    return [math.floor(seeded_random(seed + i * 13 + 7) * 10) for i in range(16)]


HIGHLIGHT_PATTERNS = [
    [5, 6, 10, 14], [1, 5, 10, 15], [0, 4, 8, 12], [3, 6, 9, 12],
    [0, 5, 10, 15], [3, 7, 10, 12], [2, 5, 9, 14]
]


def get_path(y, m, d, type_):
    seed = chart_index(y, m, d, type_)
    return HIGHLIGHT_PATTERNS[abs(seed) % len(HIGHLIGHT_PATTERNS)]


def chart_stats(nums, path):
    counts = {}
    for n in nums:
        counts[n] = counts.get(n, 0) + 1

    repeated = sorted([n for n, c in counts.items() if c > 1])
    even = sum(1 for n in nums if n % 2 == 0)
    odd = len(nums) - even
    row_sums = [sum(nums[r * 4:r * 4 + 4]) for r in range(4)]
    max_row = row_sums.index(max(row_sums))
    min_row = row_sums.index(min(row_sums))
    active = [nums[i] for i in path]

    return {
        "repeated": repeated, "even": even, "odd": odd,
        "maxRow": max_row + 1, "minRow": min_row + 1, "active": active
    }


def chart_html(y, m, d, type_, date_long):
    is_mtp = type_ == "mtp"
    nums = generate_matrix(y, m, d, type_)
    path = get_path(y, m, d, type_)

    cells = "".join(
        f'<div class="cell{" active" if i in path else ""}">{n}</div>'
        for i, n in enumerate(nums)
    )

    heading = "RAMALAN 4D MTP & SGP" if is_mtp else "CARTA RAMALAN GDL PERDANA"
    cls = "mtp" if is_mtp else "gdl"

    return (
        f'<div class="chart-shell"><div class="chart {cls}">'
        f'<div class="chart-heading">{heading}</div>'
        f'<div class="chart-date">{date_long}</div>'
        f'<div class="matrix">{cells}</div>'
        f'<div class="chart-note">Carta Lotto dated layout — not an official result</div>'
        f'<div class="watermark">CARTALOTTO.COM</div>'
        f'</div></div>'
    )


# ---------- editorial angle rotation, ported from the homepage ----------

GDL_ANGLES = [
    "Today's GDL Perdana entry presents Carta Lotto's dated four-by-four number layout.",
    "This GDL Perdana page brings the current number layout together with its exact publishing date.",
    "The GDL Perdana chart below reflects this date's organized Carta Ramalan 4D layout.",
    "This dated GDL Perdana page provides a clear view of the day's number layout.",
    "Today's Carta Ramalan GDL Perdana entry is shown below, organized by its publishing date.",
    "This GDL Perdana update presents the current dated 4D number layout in full.",
    "The GDL Perdana grid for this date is displayed below with its complete layout.",
    "This page records the GDL Perdana entry as part of the permanent dated archive.",
    "The GDL Perdana layout for this date is organized around its exact publishing date below.",
    "This dated entry captures the GDL Perdana four-by-four number layout."
]

MTP_ANGLES = [
    "This Ramalan 4D MTP & SGP entry presents Carta Lotto's scheduled dated number layout.",
    "This MTP & SGP page brings the current number layout together with its scheduled publishing date.",
    "The MTP & SGP chart below reflects this date's scheduled Carta Ramalan 4D layout.",
    "This dated MTP & SGP page provides a clear view of the day's scheduled layout.",
    "The Ramalan 4D MTP & SGP entry is shown below, organized by its scheduled date.",
    "This MTP & SGP update presents the current dated 4D number layout in full.",
    "The MTP & SGP grid for this scheduled date is displayed below with its complete layout.",
    "This page records the MTP & SGP entry as part of the permanent dated archive."
]


def stats_sentence(stats):
    if stats["repeated"]:
        repeated_text = "Digits " + ", ".join(str(n) for n in stats["repeated"]) + " repeat within the sixteen positions."
    else:
        repeated_text = "No digit repeats among the sixteen displayed positions."

    active_text = ", ".join(str(n) for n in stats["active"])

    return (
        f"Highlighted positions show {active_text}. {repeated_text} "
        f"Row {stats['maxRow']} carries the highest simple total and row {stats['minRow']} "
        f"the lowest, with {stats['even']} even and {stats['odd']} odd values across the grid."
    )


def build_intro(y, m, d, type_):
    angles = MTP_ANGLES if type_ == "mtp" else GDL_ANGLES
    seed = abs(chart_index(y, m, d, type_))
    angle = angles[seed % len(angles)]
    nums = generate_matrix(y, m, d, type_)
    path = get_path(y, m, d, type_)
    stats = chart_stats(nums, path)
    return angle + " " + stats_sentence(stats)


# ==========================================================
# CREATE MISSING TODAY PAGES
# ==========================================================

def render_new_page(template_text, prefix, archive_date, type_):
    y, m, d = archive_date.year, archive_date.month, archive_date.day
    date_long = format_long(archive_date)
    date_iso = archive_date.isoformat()

    is_mtp = type_ == "mtp"
    title = (
        f"Ramalan 4D MTP & SGP Chart — {date_long}" if is_mtp
        else f"Carta Ramalan GDL Perdana Chart — {date_long}"
    )

    html = template_text
    html = html.replace("{{TITLE}}", title)
    html = html.replace("{{DATE_LONG}}", date_long)
    html = html.replace("{{DATE_DISPLAY}}", date_long)
    html = html.replace("{{DATE}}", date_iso)
    html = html.replace("{{CHART_HTML}}", chart_html(y, m, d, type_, date_long))
    html = html.replace("{{INTRO}}", build_intro(y, m, d, type_))

    # Previous/Next filled in properly by repair_category() right after
    # creation, so a safe placeholder default is used here.
    html = html.replace("{{PREVIOUS_URL}}", "/")
    html = html.replace("{{NEXT_URL}}", "/")

    return html


def create_missing_today():
    CHARTS.mkdir(exist_ok=True)
    today = today_myt()

    jobs = [(GDL_PREFIX, GDL_TEMPLATE, "gdl", True)]
    if is_mtp_day(today):
        jobs.append((MTP_PREFIX, MTP_TEMPLATE, "mtp", True))

    for prefix, template_path, type_, should_run in jobs:
        if not should_run:
            continue

        filename = f"{prefix}-{today.isoformat()}.html"
        target = CHARTS / filename

        if target.exists():
            print(f"Already exists, skipping: {filename}")
            continue

        if not template_path.exists():
            print(f"WARNING: template not found, cannot create {filename}: {template_path}")
            continue

        template_text = template_path.read_text(encoding="utf-8")
        rendered = render_new_page(template_text, prefix, today, type_)

        target.write_text(rendered, encoding="utf-8")
        print(f"Created: {filename}")


# ==========================================================
# MAINTAIN (repair canonical / og:url / navigation)
# unchanged logic from the existing script
# ==========================================================

def parse_archive_date(filename, prefix):
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d{{4}}-\d{{2}}-\d{{2}})\.html$")
    match = pattern.match(filename)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def archive_url(prefix, archive_date):
    return f"{SITE}/charts/{prefix}-{archive_date.isoformat()}.html"


def existing_archive_pages(prefix):
    today = today_myt()
    pages = []

    if not CHARTS.exists():
        return pages

    for path in CHARTS.glob("*.html"):
        archive_date = parse_archive_date(path.name, prefix)
        if archive_date is None:
            continue
        if archive_date > today:
            print(f"Future page ignored: {path.name}")
            continue
        pages.append((archive_date, path))

    pages.sort(key=lambda item: item[0])
    return pages


def navigation_html(prefix, previous_date, next_date):
    if previous_date:
        previous_button = f'''
<a class="btn previous" href="{archive_url(prefix, previous_date)}">
  ← Previous
</a>
'''
    else:
        previous_button = "<span></span>\n"

    if next_date:
        next_button = f'''
<a class="btn next" href="{archive_url(prefix, next_date)}">
  Next →
</a>
'''
    else:
        next_button = "<span></span>\n"

    return f'''
<nav class="post-navigation" aria-label="Archive post navigation">
  <div class="nav-label">Browse archive entries</div>
  <div class="actions">
    {previous_button}
    <a class="btn home" href="/">Home</a>
    {next_button}
  </div>
</nav>
'''


def repair_canonical(html, prefix, archive_date):
    correct_url = archive_url(prefix, archive_date)
    canonical_pattern = re.compile(
        r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']+["\']\s*/?>',
        re.IGNORECASE
    )
    replacement = f'<link\n  rel="canonical"\n  href="{correct_url}"\n>'
    if canonical_pattern.search(html):
        html = canonical_pattern.sub(replacement, html, count=1)
    return html


def repair_og_url(html, prefix, archive_date):
    correct_url = archive_url(prefix, archive_date)
    pattern = re.compile(
        r'<meta\s+property=["\']og:url["\']\s+content=["\'][^"\']+["\']\s*/?>',
        re.IGNORECASE
    )
    replacement = f'<meta\n  property="og:url"\n  content="{correct_url}"\n>'
    if pattern.search(html):
        html = pattern.sub(replacement, html, count=1)
    return html


def repair_navigation(html, prefix, previous_date, next_date):
    new_navigation = navigation_html(prefix, previous_date, next_date)

    nav_pattern = re.compile(
        r'<nav\s+class=["\']post-navigation["\'].*?</nav>',
        re.IGNORECASE | re.DOTALL
    )
    if nav_pattern.search(html):
        return nav_pattern.sub(new_navigation, html, count=1)

    actions_pattern = re.compile(
        r'<div\s+class=["\']actions["\']>.*?</div>',
        re.IGNORECASE | re.DOTALL
    )
    if actions_pattern.search(html):
        return actions_pattern.sub(new_navigation, html, count=1)

    print("Navigation block not found.")
    return html


def remove_unwanted_lines(html):
    patterns = [
        re.compile(r'<p\s+class=["\']chart-numbers["\']>.*?</p>', re.IGNORECASE | re.DOTALL),
        re.compile(r'Displayed digits:\s*[^<\n]+', re.IGNORECASE)
    ]
    for pattern in patterns:
        html = pattern.sub("", html)
    return html


def unresolved_placeholders(html):
    return sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", html)))


def repair_category(prefix):
    pages = existing_archive_pages(prefix)
    if not pages:
        print(f"No usable archive pages found: {prefix}")
        return

    dates = [item[0] for item in pages]

    for index, (archive_date, path) in enumerate(pages):
        previous_date = dates[index - 1] if index > 0 else None
        next_date = dates[index + 1] if index < len(dates) - 1 else None

        html = path.read_text(encoding="utf-8")
        html = remove_unwanted_lines(html)
        html = repair_canonical(html, prefix, archive_date)
        html = repair_og_url(html, prefix, archive_date)
        html = repair_navigation(html, prefix, previous_date, next_date)

        placeholders = unresolved_placeholders(html)
        if placeholders:
            print(f"WARNING: {path.name}")
            print("Unresolved placeholders:", ", ".join(placeholders))

        path.write_text(html, encoding="utf-8")
        print(f"Updated: {path.name}")


def show_future_files():
    today = today_myt()
    for prefix in (GDL_PREFIX, MTP_PREFIX):
        for path in CHARTS.glob(f"{prefix}-*.html"):
            archive_date = parse_archive_date(path.name, prefix)
            if archive_date and archive_date > today:
                print("Future-dated file excluded:", path.name)


def main():
    print("Carta Lotto archive: create + maintain")
    print("Today (MYT):", today_myt().isoformat())
    print()

    print("Step 1: creating today's missing pages...")
    create_missing_today()
    print()

    print("Step 2: maintaining GDL archive...")
    repair_category(GDL_PREFIX)
    print()

    print("Step 3: maintaining MTP/SGP archive...")
    repair_category(MTP_PREFIX)
    print()

    show_future_files()
    print()
    print("Done. New pages are created only for today (MYT), never for future dates.")


if __name__ == "__main__":
    main()
