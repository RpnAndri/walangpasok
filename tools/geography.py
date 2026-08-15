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
) -> list[str]:
    """
    Expand a province/region into its municipalities.

    For municipality/city, simply return itself.
    """

    if scope in (
        "municipality",
        "city",
    ):
        return [location]

    if scope == "province":
        return GEOGRAPHY.get(
            location,
            [],
        )

    # We'll add region expansion later.
    if scope == "region":
        return []

    if scope == "nationwide":
        all_municipalities = []

        for municipalities in GEOGRAPHY.values():
            all_municipalities.extend(
                municipalities
            )

        return all_municipalities

    return []