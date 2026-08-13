import re
from datetime import datetime
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup


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


def get_page(url: str) -> str:
    response = httpx.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        },
        timeout=15,
        follow_redirects=True,
    )

    response.raise_for_status()

    return response.text


def find_gma_article(date: str) -> str | None:
    """
    Find the GMA Walang Pasok article for the given date.

    Returns:
        The article URL if a matching article is found.
        None otherwise.
    """

    search_url = get_gma_search_url(date)

    html = get_page(search_url)

    soup = BeautifulSoup(html, "html.parser")
    print(soup.prettify())

    expansion_area = soup.find(
        "div",
        class_="gsc-expansionArea",
    )

    if expansion_area is None:
        return None

    results = expansion_area.find_all(
        "div",
        class_="gsc-webResult gsc-result",
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

    for result in results:

        title = result.find(
            "a",
            class_="gs-title",
        )

        if title is None:
            continue

        title_text = title.get_text(
            " ",
            strip=True,
        )

        print(f"Checking: {title_text}")

        if date_text.lower() not in title_text.lower():
            continue

        href = title.get("href")

        if href:
            return href

    return None


def article_contains_municipality(
    article_url: str,
    municipality: str,
) -> bool:

    html = get_page(article_url)

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(
        separator=" ",
        strip=True,
    )

    return municipality.lower() in text.lower()


def wp_checker(date: str, municipality: str) -> bool:
    """
    Given a date and a municipality, determine if there are classes or not.
    """

    article_url = find_gma_article(date)

    if article_url is None:
        return False

    return article_contains_municipality(
        article_url,
        municipality,
    )

article = find_gma_article("2026-08-13")

print(article)