import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE = (
    BASE_DIR
    / "data"
    / "philippines.geojson"
)

OUTPUT = (
    BASE_DIR
    / "data"
    / "ncr.geojson"
)


def is_ncr(feature: dict) -> bool:

    properties = feature.get(
        "properties",
        {},
    )

    region = (
        properties.get("region_name")
        or ""
    ).strip().lower()

    return region in {
        "national capital region",
        "metro manila",
        "ncr",
    }


with open(
    SOURCE,
    "r",
    encoding="utf-8",
) as f:
    geojson = json.load(f)


features = [
    feature
    for feature in geojson.get(
        "features",
        []
    )
    if is_ncr(feature)
]


ncr_geojson = {
    "type": "FeatureCollection",
    "features": features,
}


with open(
    OUTPUT,
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        ncr_geojson,
        f,
        ensure_ascii=False,
    )


print(
    f"Found {len(features)} NCR municipalities/cities."
)

print(
    f"Saved to: {OUTPUT}"
)