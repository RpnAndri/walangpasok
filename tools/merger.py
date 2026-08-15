from .geography import expand_location
from .nlp import SuspensionExtraction

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
        )

        for location in locations:

            results.append({
                "location": location["location"],
                "scope": "municipality",
                "province": location["province"],
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

    grouped: dict[str, list[str]] = {}

    for source in sources:

        for result in source:

            if result["status"] != "suspended":
                continue

            municipality = result["location"]

            province = result.get(
                "province"
            )

            if not province:
                province = "Unknown"

            province = normalize_province(
                province
            )

            grouped.setdefault(
                province,
                [],
            )

            if municipality not in grouped[
                province
            ]:
                grouped[
                    province
                ].append(
                    municipality
                )

    return grouped