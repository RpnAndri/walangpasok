import re
from datetime import datetime
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


GMA_SEARCH_URL = "https://www.gmanetwork.com/news/search/"


def get_gma_search_url(date: str) -> str:
    """
    Create the GMA search URL for a specific date.
    """

    dt = datetime.strptime(date, "%Y-%m-%d")

    search_query = (
        f"walang pasok "
        f"{dt.strftime('%B')} "
        f"{dt.day}, "
        f"{dt.year}"
    )

    return (
        f"{GMA_SEARCH_URL}"
        f"?search_it"
        f"#gsc.tab=0"
        f"&gsc.q={quote(search_query)}"
        f"&gsc.sort="
    )


async def get_page(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=15,
        follow_redirects=True,
    ) as client:

        response = await client.get(url)

        response.raise_for_status()

        return response.text

async def get_gma_search_results(url: str) -> list[str]:
    """
    Load a GMA search page and return the first 5 result URLs.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome"
        )

        page = await browser.new_page()

        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        # Wait for Google Custom Search results
        await page.wait_for_selector(
            ".gsc-expansionArea",
            timeout=15_000,
        )

        results = page.locator(
            ".gsc-expansionArea "
            ".gsc-webResult.gsc-result"
        )

        urls = []

        for i in range(
            min(await  results.count(), 5)
        ):
            result = results.nth(i)

            # Don't wait indefinitely for gs-title.
            title = result.locator(
                "a.gs-title"
            ).first

            if not await title.is_visible(
                timeout=5_000
            ):
                # print(
                #     f"Result {i}: no visible title"
                # )
                continue

            href = await title.get_attribute(
                "href"
            )

            # print(
            #     f"Result {i}: {href}"
            # )

            if href:
                urls.append(href)

        await browser.close()

        return urls

async def find_gma_article(
    date: str,
) -> tuple[str, str] | None:
    """
    Search GMA for an article matching the given date.

    Returns:
        (article_url, article_html)

    Returns None if no matching article is found.
    """


    search_url = get_gma_search_url(date)

    result_urls = await get_gma_search_results(
        search_url
    )

    target_date = datetime.strptime(
        date,
        "%Y-%m-%d",
    )

    date_text = (
        f"{target_date.strftime('%B')} "
        f"{target_date.day}, "
        f"{target_date.year}"
    )

    for url in result_urls:
        print(f"Checking article: {url}")
        html = await get_page(url)

        soup = BeautifulSoup(html, "html.parser")

        title = None

        for header in soup.find_all("header"):
            h1 = header.find("h1")

            if h1 is not None:
                title = h1
                break

        if title is None:
            print("No article title found")
            continue

        title_text = title.get_text(
            " ",
            strip=True,
        )

        print(f"Title: {title_text}")

        if date_text.lower() not in title_text.lower():
            print(f"Date {date_text} not found")
            continue

        print("MATCH!")

        return (
            str(url),
            html,
        )

    return None


def gma_scrape_suspended_municipalities(
    article_html: str,
) -> dict[str, list[str]]:
    """
    Scrape municipalities from a GMA Walang Pasok article.

    Supports both common GMA formats.

    Format A:

        <p><strong>Cavite</strong></p>
        <ul>
            <li>Bacoor - No face-to-face classes...</li>
            <li>Cavite City - All Levels...</li>
        </ul>

    Format B:

        <p><strong>Benguet</strong></p>

        <p>Pre-school to Senior High School</p>
        <ul>
            <li>Atok</li>
            <li>Kabayan</li>
            <li>Kibungan</li>
            <li>Tublay</li>
        </ul>

        <p>Pre-school to elementary</p>
        <ul>
            <li>Bakun</li>
            <li>Bokod</li>
            <li>Buguias</li>
            <li>Mankayan</li>
        </ul>

    The current region remains active until another
    <p><strong>...</strong></p> region heading appears.
    """

    soup = BeautifulSoup(
        article_html,
        "html.parser",
    )

    story_main = soup.find(
        "div",
        class_="story_main",
    )

    if story_main is None:
        return {}

    municipalities: dict[str, list[str]] = {}

    current_region: str | None = None

    # --------------------------------------------------
    # Process all P and UL elements in document order.
    # --------------------------------------------------

    elements = story_main.find_all(
        ["p", "ul"]
    )

    for element in elements:

        # ==================================================
        # PARAGRAPH
        # ==================================================

        if element.name == "p":

            strong = element.find(
                "strong"
            )

            # ----------------------------------------------
            # Region heading
            # ----------------------------------------------

            if strong is not None:

                region_name = strong.get_text(
                    " ",
                    strip=True,
                )

                if not region_name:
                    continue

                normalized = (
                    region_name
                    .strip()
                    .lower()
                )

                # Ignore unrelated sections
                if normalized in {
                    "schools",
                    "school",
                    "universities",
                    "university",
                }:
                    current_region = None
                    continue

                if "gma news" in normalized:
                    current_region = None
                    continue

                current_region = region_name.strip()

                municipalities.setdefault(
                    current_region,
                    [],
                )

                print(
                    f"GMA region detected: "
                    f"{current_region}"
                )

            # ----------------------------------------------
            # Plain paragraphs are things like:
            #
            # Pre-school to Senior High School
            # Pre-school to elementary
            #
            # They do NOT change the region.
            # ----------------------------------------------

            continue

        # ==================================================
        # UNORDERED LIST
        # ==================================================

        if element.name != "ul":
            continue

        if current_region is None:
            continue

        # --------------------------------------------------
        # Only direct <li> children.
        # --------------------------------------------------

        for li in element.find_all(
            "li",
            recursive=False,
        ):

            # ----------------------------------------------
            # Don't accidentally process nested lists.
            # ----------------------------------------------

            nested_ul = li.find("ul")

            if nested_ul is not None:
                # This is a parent list item rather than
                # an actual municipality entry.
                continue

            text = li.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            municipality: str | None = None

            # ==================================================
            # FORMAT A
            #
            # Bacoor - No face-to-face classes...
            # ==================================================

            match = re.match(
                r"^\s*(.+?)\s*[-–—]\s+",
                text,
            )

            if match:

                municipality = (
                    match.group(1)
                    .strip()
                )

            # ==================================================
            # FORMAT B
            #
            # Atok
            # Kabayan
            # Mankayan
            #
            # No suspension description after it.
            # ==================================================

            else:

                municipality = text.strip()

            if not municipality:
                continue

            # --------------------------------------------------
            # Avoid duplicate municipalities when the same
            # municipality appears in multiple suspension
            # categories.
            # --------------------------------------------------

            if municipality not in municipalities[
                current_region
            ]:

                municipalities[
                    current_region
                ].append(
                    municipality
                )

    # --------------------------------------------------
    # Remove regions with no municipalities.
    # --------------------------------------------------

    municipalities = {
        region: values
        for region, values in municipalities.items()
        if values
    }

    return municipalities
