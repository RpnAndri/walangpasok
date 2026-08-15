import re

from .geography import expand_location
from .nlp import SuspensionExtraction

# ==========================================================
# Municipality normalization
# ==========================================================

MUNICIPALITY_ALIASES = {
    # Cavite
    "city of cavite": "Cavite City",
    "cavite city": "Cavite City",

    # Manila
    "city of manila": "Manila",
    "manila": "Manila",
}

def normalize_municipality_name(
    location: str,
) -> str:
    """
    Normalize municipality/city names coming from
    GMA, Rappler deterministic scraping, and NLP.

    Examples:

        Lingayen (public schools only)
            -> Lingayen

        City of Cavite
            -> Cavite City

        Cavite City
            -> Cavite City

        City of Manila
            -> Manila

        Manila
            -> Manila
    """

    name = location.strip()

    # ------------------------------------------------------
    # Remove trailing parenthetical qualifiers.
    #
    # Example:
    #
    # Lingayen (public schools only)
    # -> Lingayen
    #
    # ------------------------------------------------------

    name = re.sub(
        r"\s*\([^)]*\)\s*$",
        "",
        name,
    ).strip()

    # ------------------------------------------------------
    # Normalize whitespace
    # ------------------------------------------------------

    name = re.sub(
        r"\s+",
        " ",
        name,
    ).strip()

    # ------------------------------------------------------
    # Alias lookup
    # ------------------------------------------------------

    normalized_key = name.lower()

    return MUNICIPALITY_ALIASES.get(
        normalized_key,
        name,
    )

def normalize_province(
    province: str,
) -> str:

    normalized = province.strip().lower()

    if normalized in {
        "ncr",
        "national capital region",
        "metro manila",
    }:
        return "Metro Manila"

    return province.strip()

def gma_to_suspensions(
    data: dict[str, list[str]],
) -> list[dict]:

    results = []

    for province, municipalities in data.items():

        for municipality in municipalities:

            results.append({
                "location": municipality,
                "scope": "municipality",
                "province": province,
                "status": "suspended",
                "source": "gma",
            })

    return results


def rappler_to_suspensions(
    data: dict[str, list[str]],
) -> list[dict]:

    results = []

    for province, municipalities in data.items():
        # Normalize NCR aliases
        if province.strip().lower() in {
            "national capital region",
            "ncr",
            "metro manila",
        }:
            province = "Metro Manila"

        for municipality in municipalities:

            results.append({
                "location": municipality,
                "scope": "municipality",
                "province": province,
                "status": "suspended",
                "source": "rappler",
            })

    return results


def nlp_to_suspensions(
    extraction: SuspensionExtraction,
) -> list[dict]:

    results = []

    for suspension in extraction.suspensions:

        locations = expand_location(
            suspension.location,
            suspension.scope,
            suspension.province,
        )

        for expanded in locations:

            results.append({
                "location": expanded["location"],
                "scope": "municipality",
                "province": expanded["province"],
                "status": suspension.status,
                "source": "rappler_nlp",
                "original_location": (
                    suspension.location
                ),
                "evidence": suspension.evidence,
            })

    return results


def merge_suspension_results(
    *sources: list[dict],
) -> dict[str, list[str]]:
    """
    Merge suspension results and group municipalities
    by province.

    Municipality names are normalized before merging.
    """

    merged: dict[str, list[str]] = {}

    for source in sources:

        for result in source:

            if result["status"] != "suspended":
                continue

            location = normalize_municipality_name(
                result["location"]
            )

            province = result.get(
                "province",
                "Unknown",
            )

            if not province:
                province = "Unknown"

            # ----------------------------------------------
            # Normalize NCR naming
            # ----------------------------------------------

            if province.lower() in {
                "ncr",
                "national capital region",
                "metro manila",
            }:
                province = "Metro Manila"

            # ----------------------------------------------
            # Create province bucket
            # ----------------------------------------------

            merged.setdefault(
                province,
                [],
            )

            # ----------------------------------------------
            # Avoid duplicates
            # ----------------------------------------------

            if location not in merged[province]:
                merged[province].append(
                    location
                )

    return merged