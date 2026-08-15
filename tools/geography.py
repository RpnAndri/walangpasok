import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "philippines_geography.json"
)

def normalize_region(
    location: str,
) -> str:

    normalized = location.strip().lower()

    if normalized in {
        "national capital region",
        "ncr",
        "metro manila",
    }:
        return "Metro Manila"

    return location.strip()

def normalize_province(
    province: str | None,
) -> str:

    if not province:
        return "Unknown"

    normalized = province.strip().lower()

    aliases = {
        "national capital region": "Metro Manila",
        "ncr": "Metro Manila",
        "metro manila": "Metro Manila",
    }

    return aliases.get(
        normalized,
        province.strip(),
    )


def normalize_location(
    location: str,
) -> str:

    return location.strip()

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
    province: str | None = None,
) -> list[dict]:

    location = location.strip()

    # =========================================
    # MUNICIPALITY / CITY
    # =========================================

    if scope in (
        "municipality",
        "city",
    ):

        return [
            {
                "location": location,
                "province": normalize_province(
                    province
                ),
            }
        ]

    # =========================================
    # PROVINCE
    # =========================================

    if scope == "province":

        province_name = normalize_province(
            location
        )

        municipalities = GEOGRAPHY.get(
            province_name,
            [],
        )

        return [
            {
                "location": municipality,
                "province": province_name,
            }
            for municipality in municipalities
        ]

    # =========================================
    # REGION
    # =========================================

    if scope == "region":

        region = location.lower().strip()

        if region in {
            "national capital region",
            "ncr",
            "metro manila",
        }:

            municipalities = GEOGRAPHY.get(
                "Metro Manila",
                [],
            )

            return [
                {
                    "location": municipality,
                    "province": "Metro Manila",
                }
                for municipality in municipalities
            ]

        return []

    # =========================================
    # NATIONWIDE
    # =========================================

    if scope == "nationwide":

        results = []

        for province_name, municipalities in (
            GEOGRAPHY.items()
        ):

            province_name = normalize_province(
                province_name
            )

            for municipality in municipalities:

                results.append({
                    "location": municipality,
                    "province": province_name,
                })

        return results

    return []