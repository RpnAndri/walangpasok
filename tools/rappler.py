import re
from datetime import datetime
from urllib.parse import quote

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .gma import get_page


RAPPLER_SEARCH_URL = "https://www.rappler.com/"


async def get_rappler_search_results(
    date: str,
) -> list[str]:
    """
    Search Rappler and return the first 5 result URLs.
    """

    dt = datetime.strptime(
        date,
        "%Y-%m-%d",
    )

    query = (
        f"walang pasok "
        f"{dt.strftime('%B')} "
        f"{dt.day} "
        f"{dt.year}"
    )

    search_url = (
        f"{RAPPLER_SEARCH_URL}"
        f"?q={quote(query)}"
        f"#gsc.tab=0"
        f"&gsc.q={quote(query)}"
        f"&gsc.page=1"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
        )

        page = await browser.new_page()

        await page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        await page.wait_for_selector(
            ".gsc-expansionArea",
            timeout=15_000,
        )

        results = page.locator(
            ".gsc-expansionArea "
            ".gsc-webResult.gsc-result"
        )

        urls: list[str] = []

        count = min(
            await results.count(),
            5,
        )

        for i in range(count):

            result = results.nth(i)

            title = result.locator(
                "a.gs-title"
            ).first

            try:
                if not await title.is_visible(
                    timeout=5_000
                ):
                    continue
            except Exception:
                continue

            href = await title.get_attribute(
                "href"
            )

            if not href:
                continue

            if not href.startswith(
                "https://www.rappler.com/"
            ):
                continue

            if href in urls:
                continue

            urls.append(href)

        await browser.close()

        return urls


def get_article_title(
    article_html: str,
) -> str | None:
    """
    Extract the Rappler article title.

    Preferred selector:
        h1.post-single_title

    Falls back to a generic h1.
    """

    soup = BeautifulSoup(
        article_html,
        "html.parser",
    )

    title = soup.find(
        "h1",
        class_="post-single_title",
    )

    if title is not None:
        return title.get_text(
            " ",
            strip=True,
        )

    # Fallback
    title = soup.find("h1")

    if title is not None:
        return title.get_text(
            " ",
            strip=True,
        )

    return None


async def find_rappler_article(
    date: str,
) -> tuple[str, str] | None:
    """
    Search Rappler and return the first article
    whose title contains the requested full date.

    Returns:
        (article_url, article_html)

    or None.
    """

    result_urls = await get_rappler_search_results(
        date
    )

    dt = datetime.strptime(
        date,
        "%Y-%m-%d",
    )

    date_text = (
        f"{dt.strftime('%B')} "
        f"{dt.day}, "
        f"{dt.year}"
    )

    for url in result_urls:

        print(
            f"Checking Rappler article: {url}"
        )

        try:
            html = await get_page(url)

        except Exception as e:
            print(
                f"Failed to fetch Rappler article: {e}"
            )
            continue

        title = get_article_title(html)

        if title is None:
            print(
                "No Rappler article title found"
            )
            continue

        print(
            f"Title: {title}"
        )

        if date_text.lower() not in title.lower():
            print(
                f"Date {date_text} not found"
            )
            continue

        print(
            "RAPPLER MATCH!"
        )

        # We already downloaded this HTML,
        # so don't download it again.
        return (
            url,
            html,
        )

    return None


def rappler_scrape_suspended_municipalities(
    article_html: str,
) -> dict[str, list[str]]:
    """
    Deterministically scrape municipality suspensions
    from a Rappler article.

    Handles structures such as:

        NCR
        └── <ul>
              ├── Malabon City
              ├── Manila
              └── Quezon City

    And nested regional structures such as:

        Calabarzon
        └── Batangas province
            └── Lian

        └── Cavite province
            └── Amadeo

    Returns:

        {
            "Metro Manila": [
                "Manila",
                "Quezon City"
            ],
            "Cavite": [
                "Amadeo"
            ],
            "Batangas": [
                "Lian"
            ]
        }
    """

    soup = BeautifulSoup(
        article_html,
        "html.parser",
    )

    content = soup.find(
        "div",
        class_="post-single__content entry-content",
    )

    if content is None:
        return {}

    municipalities: dict[str, list[str]] = {}

    current_region: str | None = None

    # ==================================================
    # HELPERS
    # ==================================================

    def add_municipality(
        province: str,
        municipality: str,
    ):
        municipality = municipality.strip()

        if not municipality:
            return

        # Remove leading bullet/dash characters
        municipality = municipality.lstrip(
            "–—-• "
        ).strip()

        if not municipality:
            return

        municipalities.setdefault(
            province,
            [],
        )

        if municipality not in municipalities[
            province
        ]:
            municipalities[
                province
            ].append(municipality)

    def clean_location(
        text: str,
    ) -> str:

        text = text.strip()

        # Remove leading bullets
        text = text.lstrip(
            "–—-• "
        ).strip()

        # Remove "province" suffix
        text = re.sub(
            r"\s+province$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        return text

    def get_li_label(
        li,
    ) -> str:

        # ------------------------------------------
        # First try an <a>
        # ------------------------------------------

        link = li.find(
            "a",
            recursive=False,
        )

        if link is not None:

            return clean_location(
                link.get_text(
                    " ",
                    strip=True,
                )
            )

        # ------------------------------------------
        # Otherwise get only direct text
        # ------------------------------------------

        direct_text = "".join(
            str(child)
            for child in li.children
            if getattr(
                child,
                "name",
                None,
            ) is None
        )

        return clean_location(
            BeautifulSoup(
                direct_text,
                "html.parser",
            ).get_text(
                " ",
                strip=True,
            )
        )

    # ==================================================
    # FIND REGION HEADINGS
    # ==================================================

    headings = content.find_all(
        "h5",
        class_="wp-block-heading",
    )

    for heading in headings:

        region = clean_location(
            heading.get_text(
                " ",
                strip=True,
            )
        )

        if not region:
            continue

        # Ignore non-location headings
        if region.lower() in {
            "schools",
            "universities",
        }:
            continue

        # Normalize NCR
        if region.lower() in {
            "ncr",
            "national capital region",
            "metro manila",
        }:
            region = "Metro Manila"

        current_region = region

        municipalities.setdefault(
            current_region,
            [],
        )

        # --------------------------------------------------
        # Find the FIRST UL after this heading.
        #
        # Stop if another heading is encountered.
        # --------------------------------------------------

        ul = heading.find_next(
            "ul",
            class_="wp-block-list",
        )

        if ul is None:
            continue

        # Make sure this UL belongs to this heading,
        # rather than some later section.
        next_heading = heading.find_next(
            "h5",
            class_="wp-block-heading",
        )

        if (
            next_heading is not None
            and ul.find_previous(
                "h5",
                class_="wp-block-heading",
            ) != heading
        ):
            continue

        # ==================================================
        # CASE 1:
        #
        # Flat list:
        #
        # <ul>
        #   <li>Manila</li>
        #   <li>Quezon City</li>
        # </ul>
        # ==================================================

        for li in ul.find_all(
            "li",
            recursive=False,
        ):

            nested_ul = li.find(
                "ul",
                recursive=False,
            )

            label = get_li_label(li)

            # ------------------------------------------
            # Nested list means this is probably a
            # province containing municipalities.
            # ------------------------------------------

            if nested_ul is not None:

                province = clean_location(
                    label
                )

                if not province:
                    continue

                for municipality_li in nested_ul.find_all(
                    "li",
                    recursive=False,
                ):

                    municipality = get_li_label(
                        municipality_li
                    )

                    # If there is another nested UL,
                    # recurse into it.
                    deeper_ul = municipality_li.find(
                        "ul",
                        recursive=False,
                    )

                    if deeper_ul is not None:

                        province_name = clean_location(
                            municipality
                        )

                        for nested_municipality_li in (
                            deeper_ul.find_all(
                                "li",
                                recursive=False,
                            )
                        ):

                            nested_municipality = (
                                get_li_label(
                                    nested_municipality_li
                                )
                            )

                            add_municipality(
                                province_name,
                                nested_municipality,
                            )

                    else:

                        add_municipality(
                            province,
                            municipality,
                        )

            # ------------------------------------------
            # Flat municipality
            # ------------------------------------------

            else:

                if label:
                    add_municipality(
                        current_region,
                        label,
                    )

    return municipalities


def rappler_get_article_text(
    article_html: str,
) -> str:
    """
    Extract the relevant Rappler article content
    to send to the NLP model.
    """

    soup = BeautifulSoup(
        article_html,
        "html.parser",
    )

    content = soup.find(
        "div",
        class_="post-single__content entry-content",
    )

    if content is None:
        return ""

    # Remove things that aren't useful to NLP.
    for element in content.find_all(
        [
            "script",
            "style",
            "noscript",
            "iframe",
        ]
    ):
        element.decompose()

    return content.get_text(
        "\n",
        strip=True,
    )