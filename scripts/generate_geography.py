import json

import httpx


URL = (
    "https://psgc.cloud/api/v2/"
    "cities-municipalities"
)


async def generate():

    async with httpx.AsyncClient(
        timeout=60,
        follow_redirects=True,
    ) as client:

        response = await client.get(URL)

        response.raise_for_status()

        payload = response.json()

    # -----------------------------------------
    # Handle API response format
    # -----------------------------------------

    if isinstance(payload, list):

        data = payload

    elif isinstance(payload, dict):

        # Some API versions/wrappers return:
        #
        # {
        #     "data": [...]
        # }

        data = payload.get(
            "data",
            [],
        )

    else:

        raise RuntimeError(
            f"Unexpected API response type: "
            f"{type(payload)}"
        )

    if not isinstance(data, list):

        raise RuntimeError(
            "Could not find a list of "
            "cities/municipalities in API response."
        )

    print(
        f"Received {len(data)} locations"
    )

    # -----------------------------------------
    # Build geography
    # -----------------------------------------

    geography: dict[str, list[str]] = {}

    for item in data:

        if not isinstance(item, dict):

            print(
                "Skipping unexpected item:",
                repr(item),
            )

            continue

        name = item.get("name")

        if not name:
            continue

        name = name.strip()

        province = item.get(
            "province"
        )

        region = item.get(
            "region"
        )

        # -------------------------------------
        # NCR
        # -------------------------------------

        if not province:

            if region:

                region_upper = (
                    region
                    .strip()
                    .upper()
                )

                if (
                    "NATIONAL CAPITAL REGION"
                    in region_upper
                    or region_upper == "NCR"
                ):

                    province = "Metro Manila"

        # -------------------------------------
        # Skip anything without a parent
        # -------------------------------------

        if not province:

            print(
                f"Skipping {name}: "
                f"no province/parent"
            )

            continue

        province = province.strip()

        # -------------------------------------
        # Add municipality/city
        # -------------------------------------

        geography.setdefault(
            province,
            [],
        )

        if name not in geography[province]:

            geography[province].append(
                name
            )

    # -----------------------------------------
    # Sort
    # -----------------------------------------

    geography = {

        province: sorted(
            municipalities,
            key=str.casefold,
        )

        for province, municipalities
        in sorted(
            geography.items(),
            key=lambda x: x[0].casefold(),
        )
    }

    # -----------------------------------------
    # Validate
    # -----------------------------------------

    total = sum(
        len(municipalities)
        for municipalities
        in geography.values()
    )

    print(
        f"Geographic groups: "
        f"{len(geography)}"
    )

    print(
        f"Cities/municipalities: "
        f"{total}"
    )

    # -----------------------------------------
    # Write JSON
    # -----------------------------------------

    with open(
        "philippines_geography.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            geography,
            f,
            ensure_ascii=False,
            indent=4,
        )

    print(
        "Generated philippines_geography.json"
    )


if __name__ == "__main__":

    import asyncio

    asyncio.run(
        generate()
    )