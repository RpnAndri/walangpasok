import json
from pathlib import Path


INPUT_DIR = Path(__file__).resolve().parent.parent / "geojson_city"
OUTPUT_FILE = Path("philippines.geojson")


def combine_geojson():
    features = []

    files = sorted(
        INPUT_DIR.glob("*.geo.json")
    )

    print(f"Found {len(files)} GeoJSON files.")

    for file in files:

        try:
            with file.open(
                "r",
                encoding="utf-8",
            ) as f:
                data = json.load(f)

        except Exception as e:
            print(
                f"Failed to read {file.name}: {e}"
            )
            continue

        # Each source file should contain
        # one GeoJSON Feature.
        if data.get("type") != "Feature":
            print(
                f"Skipping {file.name}: "
                f"expected Feature, got "
                f"{data.get('type')}"
            )
            continue

        properties = data.get(
            "properties",
            {},
        )

        city = properties.get(
            "city_name"
        )

        province = properties.get(
            "province_name"
        )

        region = properties.get(
            "region_name"
        )

        if not city or not province:
            print(
                f"Warning: {file.name} "
                f"is missing city/province"
            )

        features.append(data)

    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print()
    print(
        f"Created {OUTPUT_FILE}"
    )
    print(
        f"Features: {len(features)}"
    )


if __name__ == "__main__":
    combine_geojson()