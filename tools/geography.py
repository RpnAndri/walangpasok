import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "philippines.geojson"
)


# =========================================================
# NORMALIZATION
# =========================================================

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


# =========================================================
# LOAD GEOJSON
# =========================================================

def load_geography() -> dict[str, list[str]]:
    """
    Load the unified Philippines GeoJSON and build:

        {
            "Cavite": [
                "Bacoor",
                "Cavite City",
                ...
            ],
            "Benguet": [
                "Atok",
                "Bakun",
                ...
            ],
            "Metro Manila": [
                "Manila",
                "Quezon City",
                ...
            ]
        }

    The GeoJSON is the single source of truth.
    """

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Expected a GeoJSON FeatureCollection"
        )

    geography: dict[str, list[str]] = {}

    for feature in data.get(
        "features",
        [],
    ):

        properties = feature.get(
            "properties",
            {},
        )

        city = properties.get(
            "city_name"
        )

        province = properties.get(
            "province_name"
        )

        if not city or not province:
            continue

        province = normalize_province(
            province
        )

        city = normalize_location(
            city
        )

        geography.setdefault(
            province,
            []
        )

        if city not in geography[province]:
            geography[province].append(
                city
            )

    return geography


GEOGRAPHY = load_geography()


# =========================================================
# EXPAND LOCATION
# =========================================================

def expand_location(
    location: str,
    scope: str,
    province: str | None = None,
) -> list[dict]:

    location = location.strip()

    # =====================================================
    # MUNICIPALITY / CITY
    # =====================================================

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

    # =====================================================
    # PROVINCE
    # =====================================================

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

    # =====================================================
    # REGION
    # =====================================================

    if scope == "region":

        normalized_region = (
            normalize_region(location)
        )

        # Metro Manila / NCR
        #
        # In the GeoJSON, NCR municipalities have
        # province_name = "Metro Manila".
        if normalized_region == "Metro Manila":

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

        # Other regions
        #
        # The GeoJSON contains region_name, so find
        # all municipalities belonging to this region.
        return expand_region(
            normalized_region
        )

    # =====================================================
    # NATIONWIDE
    # =====================================================

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


# =========================================================
# REGION EXPANSION
# =========================================================

def expand_region(
    region: str,
) -> list[dict]:
    """
    Find all municipalities belonging to a region
    directly from the GeoJSON.

    This does NOT depend on philippines_geography.json.
    """

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    normalized_target = (
        region.strip().lower()
    )

    results = []

    for feature in data.get(
        "features",
        [],
    ):

        properties = feature.get(
            "properties",
            {},
        )

        city = properties.get(
            "city_name"
        )

        province = properties.get(
            "province_name"
        )

        region_name = properties.get(
            "region_name"
        )

        if not city or not province:
            continue

        if not region_name:
            continue

        if (
            region_name.strip().lower()
            != normalized_target
        ):
            continue

        results.append({
            "location": city.strip(),
            "province": normalize_province(
                province
            ),
        })

    return results