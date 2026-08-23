import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


API_BASE = "https://api.demonlist.org"

USER_API = f"{API_BASE}/user/get"
RECORD_API = f"{API_BASE}/user/record/list"
LEVEL_API = f"{API_BASE}/level/classic/getCache"

OUTPUT_FILE = Path("data/players.json")


PLAYERS = {
    "went1xgmd": 38987,
    "Magnum": 18356,
    "Zafsa": 18651,
    "Vanchos": 18210,
    "Фанат Абстракта": 951,
    "arslnxx": 19027,
    "SashaKray": 7560,
    "Amabest": 29826,
    "LoyalVladik": 21713,
    "egyssgd": 31906,
    "Velance": 24510,
    "ferux": 33994,
    "Mateex": 6053,
    "forewad": 21129,
    "CosmoReator": 24070,
    "noN2me": 28295,
    "M Ok You": 41742,
    "mirageee": 28256,
    "Stylish": 2629,
    "meyv": 37330,
    "Redis_GD435": 21222,
    "Kinoxas": 26120,
    "clandd": 29605,
    "Skraity": 28896,
    "StintlerGD": 18689,
    "z0n1x": 26345,
    "Tanker674": 26186,
    "Paberik": 31056,
    "JabkaGD": 3912,
    "n0rmalGD": 29533,
}


session = requests.Session()

session.headers.update({
    "User-Agent": "GlobalDemonlistPlayerTracker/1.0"
})


def request_json(url, params):

    response = session.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if result.get("message") != "success":
        raise RuntimeError(
            f"API returned: {result.get('message')}"
        )

    return result["data"]


def get_player(user_id):

    return request_json(
        USER_API,
        {
            "id": user_id
        }
    )


def get_records(user_id):

    records = []

    offset = 0
    limit = 50

    while True:

        data = request_json(
            RECORD_API,
            {
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            }
        )

        page = data.get("records", [])

        records.extend(page)

        total = data.get(
            "total_count",
            len(records)
        )

        if len(records) >= total:
            break

        if not page:
            break

        offset += limit

        time.sleep(0.1)

    return records


def get_level(level_id):

    try:

        return request_json(
            LEVEL_API,
            {
                "id": level_id
            }
        )

    except Exception as error:

        print(
            f"      Could not fetch level "
            f"{level_id}: {error}"
        )

        return None


def clean_level(record):

    level = record.get("level") or {}

    level_id = level.get("id")

    detailed = None

    if level_id:
        detailed = get_level(level_id)

    if detailed:

        level_name = detailed.get(
            "name",
            level.get("name")
        )

        placement = detailed.get(
            "placement",
            level.get("placement")
        )

        points = detailed.get("points")

        ingame_id = detailed.get(
            "ingame_id"
        )

        creator = detailed.get(
            "creator"
        )

        holder = detailed.get(
            "holder"
        )

        verification_url = (
            detailed
            .get("verification", {})
            .get("video_url")
        )

    else:

        level_name = level.get("name")
        placement = level.get("placement")
        points = None
        ingame_id = None
        creator = None
        holder = None
        verification_url = None

    return {

        "id": level_id,

        "ingame_id": ingame_id,

        "name": level_name,

        "placement": placement,

        "points": points,

        "creator": creator,

        "holder": holder,

        "verification_url": verification_url,

        "level_url": (
            f"https://demonlist.org/classic/{level_id}"
            if level_id
            else None
        ),

        "video_url": record.get(
            "video_url"
        ),

        "percent": record.get(
            "percent"
        ),

        "status": record.get(
            "status"
        )

    }


def main():

    players = {}

    print("Updating Global Demonlist...")
    print()

    for expected_name, user_id in PLAYERS.items():

        print(
            f"Fetching {expected_name} "
            f"(ID: {user_id})..."
        )

        try:

            profile = get_player(user_id)

            raw_records = get_records(user_id)

            completed_records = [
                record
                for record in raw_records
                if (
                    record.get("percent") == 100
                    and record.get("status") == "accepted"
                )
            ]

            print(
                f"  Found "
                f"{len(completed_records)} "
                f"completed levels"
            )

            completed_levels = []

            for record in completed_records:

                level = clean_level(record)

                completed_levels.append(level)

                time.sleep(0.08)

            points = profile.get("points")

            if points is not None:
                points = float(points)

            players[expected_name] = {

                "id": user_id,

                "username": profile.get(
                    "username"
                ),

                # Global Demonlist placement
                "global_placement": profile.get(
                    "placement"
                ),

                "points": points,

                "country": profile.get(
                    "country"
                ),

                "badge": profile.get(
                    "badge"
                ),

                "is_banned": profile.get(
                    "is_banned"
                ),

                "completed_levels":
                    completed_levels

            }

            print(
                f"  Global: "
                f"#{profile.get('placement')} | "
                f"{points} points"
            )

        except Exception as error:

            print(
                f"  ERROR: {error}"
            )

            players[expected_name] = {

                "id": user_id,

                "username": expected_name,

                "global_placement": None,

                "points": None,

                "country": None,

                "badge": None,

                "is_banned": None,

                "completed_levels": [],

                "error": str(error)

            }

        print()

        time.sleep(0.2)

    output = {

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "players": players

    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Finished! Saved to "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
