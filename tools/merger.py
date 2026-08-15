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

    merged: dict[str, list[str]] = {}

    for source in sources:

        for result in source:

            if result["status"] != "suspended":
                continue

            location = result["location"].strip()

            province = result.get(
                "province"
            )

            # =====================================
            # NORMALIZE PROVINCE
            # =====================================

            if province:

                normalized = province.strip().lower()

                if normalized in {
                    "national capital region",
                    "ncr",
                    "metro manila",
                }:
                    province = "Metro Manila"

                else:
                    province = province.strip()

            else:
                province = "Unknown"

            # =====================================
            # CREATE PROVINCE GROUP
            # =====================================

            merged.setdefault(
                province,
                [],
            )

            # =====================================
            # AVOID DUPLICATES
            # =====================================

            if location not in merged[province]:

                merged[province].append(
                    location
                )

    return merged