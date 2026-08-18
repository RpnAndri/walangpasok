from .gma import (
    find_gma_article,
    gma_scrape_suspended_municipalities,
)

from .rappler import (
    find_rappler_article,
    rappler_scrape_suspended_municipalities,
    rappler_get_article_text,
)

from .nlp import extract_suspensions

from .merger import (
    gma_to_suspensions,
    rappler_to_suspensions,
    nlp_to_suspensions,
    merge_suspension_results,
)


async def wp_checker(
    date: str,
) -> dict:
    """
    Collect class suspension information from:

    1. GMA deterministic scraper
    2. Rappler deterministic scraper
    3. Rappler NLP extraction

    Then merge all results into a province/region-grouped
    municipality dictionary.

    Returns:

    {
        "date": "2026-08-14",
        "municipalities": {
            "Cavite": [
                "Bacoor",
                "Cavite City",
                "Kawit"
            ],
            "Metro Manila": [
                "Manila",
                "Quezon City"
            ]
        }
    }
    """

    # ==================================================
    # GMA
    # ==================================================

    gma_results = []

    try:

        gma_article = await find_gma_article(
            date
        )

        if gma_article is not None:

            gma_url, gma_html = gma_article

            print(
                f"GMA article found: {gma_url}"
            )

            gma_data = (
                gma_scrape_suspended_municipalities(
                    gma_html
                )
            )

            print(
                f"GMA municipalities: {gma_data}"
            )

            gma_results = (
                gma_to_suspensions(
                    gma_data
                )
            )

        else:

            print(
                "No GMA article found."
            )

    except Exception as e:

        print(
            f"GMA scraper failed: {e}"
        )


    # ==================================================
    # RAPPLEr
    # ==================================================

    rappler_results = []
    rappler_nlp_results = []

    try:

        rappler_article = await find_rappler_article(
            date
        )

        if rappler_article is not None:

            rappler_url, rappler_html = (
                rappler_article
            )

            print(
                f"Rappler article found: {rappler_url}"
            )

            # ------------------------------------------
            # Deterministic Rappler
            # ------------------------------------------

            rappler_data = (
                rappler_scrape_suspended_municipalities(
                    rappler_html
                )
            )

            print(
                f"Rappler municipalities: {rappler_data}"
            )

            rappler_results = (
                rappler_to_suspensions(
                    rappler_data
                )
            )

            # ------------------------------------------
            # Rappler NLP
            # ------------------------------------------

            article_text = (
                rappler_get_article_text(
                    rappler_html
                )
            )

            if article_text:

                print(
                    "Sending Rappler article to NLP..."
                )

                extraction = (
                    await extract_suspensions(
                        article_text
                    )
                )

                rappler_nlp_results = (
                    nlp_to_suspensions(
                        extraction
                    )
                )

                # print(
                #     "Rappler NLP results:",
                #     rappler_nlp_results,
                # )

        else:

            print(
                "No Rappler article found."
            )

    except Exception as e:

        print(
            f"Rappler scraper failed: {e}"
        )


    # ==================================================
    # MERGE
    # ==================================================

    municipalities = merge_suspension_results(
        gma_results,
        rappler_results,
        rappler_nlp_results,
    )


    # ==================================================
    # RETURN
    # ==================================================

    print(municipalities)

    return {
        "date": date,
        "municipalities": municipalities,
    }


# result = wp_checker("2026-08-13")

# import json
# print(json.dumps(result, indent=4, ensure_ascii=False))