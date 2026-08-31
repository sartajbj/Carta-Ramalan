from pathlib import Path
from datetime import date, datetime
import re

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"

SITE = "https://www.cartalotto.com"

GDL_PREFIX = "carta-ramalan-gdl-perdana"
MTP_PREFIX = "ramalan-4d-mtp-sgp"


def parse_archive_date(filename, prefix):
    """
    Example:
    carta-ramalan-gdl-perdana-2026-08-31.html
    """

    pattern = re.compile(
        rf"^{re.escape(prefix)}-(\d{{4}}-\d{{2}}-\d{{2}})\.html$"
    )

    match = pattern.match(filename)

    if not match:
        return None

    try:
        return datetime.strptime(
            match.group(1),
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return None


def archive_url(prefix, archive_date):
    return (
        f"{SITE}/charts/"
        f"{prefix}-{archive_date.isoformat()}.html"
    )


def existing_archive_pages(prefix):
    """
    Return existing CURRENT/PAST archive pages only.

    Future-dated files are intentionally excluded
    from navigation.
    """

    today = date.today()
    pages = []

    if not CHARTS.exists():
        return pages

    for path in CHARTS.glob("*.html"):

        archive_date = parse_archive_date(
            path.name,
            prefix
        )

        if archive_date is None:
            continue

        if archive_date > today:
            print(
                f"Future page ignored: {path.name}"
            )
            continue

        pages.append(
            (archive_date, path)
        )

    pages.sort(
        key=lambda item: item[0]
    )

    return pages


def navigation_html(
    prefix,
    previous_date,
    next_date
):
    """
    Build Previous / Home / Next navigation.

    Buttons are shown only when the corresponding
    existing archive page is available.
    """

    if previous_date:

        previous_button = f"""
<a
  class="btn previous"
  href="{archive_url(prefix, previous_date)}">
  ← Previous
</a>
"""

    else:

        previous_button = """
<span></span>
"""


    if next_date:

        next_button = f"""
<a
  class="btn next"
  href="{archive_url(prefix, next_date)}">
  Next →
</a>
"""

    else:

        next_button = """
<span></span>
"""


    return f"""
<nav
  class="post-navigation"
  aria-label="Archive post navigation">

  <div class="nav-label">
    Browse archive entries
  </div>

  <div class="actions">

    {previous_button}

    <a
      class="btn home"
      href="/">
      Home
    </a>

    {next_button}

  </div>

</nav>
"""


def repair_canonical(
    html,
    prefix,
    archive_date
):
    """
    Ensure canonical URL points to the real
    .html archive file.
    """

    correct_url = archive_url(
        prefix,
        archive_date
    )

    canonical_pattern = re.compile(
        r'<link\s+rel=["\']canonical["\']\s+'
        r'href=["\'][^"\']+["\']\s*/?>',
        re.IGNORECASE
    )

    replacement = (
        '<link\n'
        '  rel="canonical"\n'
        f'  href="{correct_url}"\n'
        '>'
    )

    if canonical_pattern.search(html):

        html = canonical_pattern.sub(
            replacement,
            html,
            count=1
        )

    return html


def repair_og_url(
    html,
    prefix,
    archive_date
):
    """
    Correct Open Graph URL when present.
    """

    correct_url = archive_url(
        prefix,
        archive_date
    )

    pattern = re.compile(
        r'<meta\s+property=["\']og:url["\']\s+'
        r'content=["\'][^"\']+["\']\s*/?>',
        re.IGNORECASE
    )

    replacement = (
        '<meta\n'
        '  property="og:url"\n'
        f'  content="{correct_url}"\n'
        '>'
    )

    if pattern.search(html):

        html = pattern.sub(
            replacement,
            html,
            count=1
        )

    return html


def repair_navigation(
    html,
    prefix,
    previous_date,
    next_date
):
    """
    Supports both:

    NEW template:
    <nav class="post-navigation">...</nav>

    OLD pages:
    <div class="actions">...</div>
    """

    new_navigation = navigation_html(
        prefix,
        previous_date,
        next_date
    )


    # New template navigation
    nav_pattern = re.compile(
        r'<nav\s+class=["\']post-navigation["\']'
        r'.*?</nav>',
        re.IGNORECASE | re.DOTALL
    )

    if nav_pattern.search(html):

        return nav_pattern.sub(
            new_navigation,
            html,
            count=1
        )


    # Older generated pages
    actions_pattern = re.compile(
        r'<div\s+class=["\']actions["\']>'
        r'.*?</div>',
        re.IGNORECASE | re.DOTALL
    )

    if actions_pattern.search(html):

        return actions_pattern.sub(
            new_navigation,
            html,
            count=1
        )


    print(
        "Navigation block not found."
    )

    return html


def remove_unwanted_lines(html):
    """
    Remove old duplicated chart-description text
    when it still exists on legacy pages.
    """

    patterns = [

        re.compile(
            r'<p\s+class=["\']chart-numbers["\']>'
            r'.*?</p>',
            re.IGNORECASE | re.DOTALL
        ),

        re.compile(
            r'Displayed digits:\s*'
            r'[^<\n]+',
            re.IGNORECASE
        )

    ]

    for pattern in patterns:

        html = pattern.sub(
            "",
            html
        )

    return html


def unresolved_placeholders(html):
    """
    Detect template tokens accidentally published
    to production.
    """

    return sorted(
        set(
            re.findall(
                r"\{\{[A-Z0-9_]+\}\}",
                html
            )
        )
    )


def repair_category(prefix):
    """
    Repair one archive category.
    """

    pages = existing_archive_pages(
        prefix
    )

    if not pages:

        print(
            f"No usable archive pages found: {prefix}"
        )

        return


    dates = [
        item[0]
        for item in pages
    ]


    for index, (archive_date, path) in enumerate(pages):

        previous_date = (
            dates[index - 1]
            if index > 0
            else None
        )

        next_date = (
            dates[index + 1]
            if index < len(dates) - 1
            else None
        )


        html = path.read_text(
            encoding="utf-8"
        )


        html = remove_unwanted_lines(
            html
        )


        html = repair_canonical(
            html,
            prefix,
            archive_date
        )


        html = repair_og_url(
            html,
            prefix,
            archive_date
        )


        html = repair_navigation(
            html,
            prefix,
            previous_date,
            next_date
        )


        placeholders = unresolved_placeholders(
            html
        )


        if placeholders:

            print(
                f"WARNING: {path.name}"
            )

            print(
                "Unresolved placeholders:",
                ", ".join(placeholders)
            )


        path.write_text(
            html,
            encoding="utf-8"
        )


        print(
            f"Updated: {path.name}"
        )


def show_future_files():
    """
    Future files are not modified automatically.
    They are only reported.
    """

    today = date.today()

    for prefix in (
        GDL_PREFIX,
        MTP_PREFIX
    ):

        for path in CHARTS.glob(
            f"{prefix}-*.html"
        ):

            archive_date = parse_archive_date(
                path.name,
                prefix
            )

            if (
                archive_date
                and archive_date > today
            ):

                print(
                    "Future-dated file excluded:",
                    path.name
                )


def main():

    if not CHARTS.exists():

        print(
            "charts directory not found."
        )

        return


    print(
        "Carta Lotto archive maintenance"
    )

    print(
        "Today:",
        date.today().isoformat()
    )

    print()


    print(
        "Checking GDL archive..."
    )

    repair_category(
        GDL_PREFIX
    )


    print()


    print(
        "Checking MTP/SGP archive..."
    )

    repair_category(
        MTP_PREFIX
    )


    print()


    show_future_files()


    print()

    print(
        "Archive maintenance completed."
    )

    print(
        "No new pages were generated."
    )

    print(
        "Future-dated pages were excluded from navigation."
    )

    print(
        "Previous/Home/Next links use existing .html pages only."
    )


if __name__ == "__main__":
    main()
