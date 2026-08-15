import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "philippines_geography.json"
)


def load_geography() -> dict[str, list[str]]:
    with open(
        DATA_FILE,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


GEOGRAPHY = load_geography()


def expand_location(
    location: str,
    scope: str,
) -> list[dict]:
    """
    Expand a province/region into its municipalities.

    Returns:
        [
            {
                "location": "Bacoor",
                "province": "Cavite",
            },
            ...
        ]

    For municipality/city, the province is looked up
    from GEOGRAPHY.
    """

    # -----------------------------------------
    # Municipality / City
    # -----------------------------------------

    if scope in (
        "municipality",
        "city",
    ):

        for province, municipalities in GEOGRAPHY.items():

            if location in municipalities:
                return [{
                    "location": location,
                    "province": province,
                }]

        # Could not determine province
        return [{
            "location": location,
            "province": "Unknown",
        }]

    # -----------------------------------------
    # Province
    # -----------------------------------------

    if scope == "province":

        municipalities = GEOGRAPHY.get(
            location,
            [],
        )

        return [
            {
                "location": municipality,
                "province": location,
            }
            for municipality in municipalities
        ]

    # -----------------------------------------
    # Region
    # -----------------------------------------

    if scope == "region":
        return []

    # -----------------------------------------
    # Nationwide
    # -----------------------------------------

    if scope == "nationwide":

        results = []

        for province, municipalities in GEOGRAPHY.items():

            for municipality in municipalities:

                results.append({
                    "location": municipality,
                    "province": province,
                })

        return results

    return []