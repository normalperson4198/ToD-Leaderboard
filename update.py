import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


API_BASE = "https://api.demonlist.org"

USER_API = f"{API_BASE}/user/get"
RECORD_API = f"{API_BASE}/user/record/list"

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


def request_json(url, params):
    response = requests.get(
        url,
        params=params,
        timeout=30,
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
        {"id": user_id},
    )


def get_all_records(user_id):
    """
    Fetch every record for a player.

    The API allows a maximum of 50 records per request,
    so we continue requesting pages until we have them all.
    """

    records = []
    offset = 0
    limit = 50

    while True:

        data = request_json(
            RECORD_API,
            {
                "user_id": user_id,
                "limit": limit,
                "offset": offset,
            },
        )

        page = data.get("records", [])

        records.extend(page)

        total_count = data.get(
            "total_count",
            len(records),
        )

        if len(records) >= total_count:
            break

        if not page:
            break

        offset += limit

        time.sleep(0.1)

    return records


def clean_record(record):
    level = record.get("level") or {}

    return {
        "id": record.get("id"),
        "percent": record.get("percent"),
        "status": record.get("status"),
        "video_url": record.get("video_url"),
        "level": {
            "id": level.get("id"),
            "name": level.get("name"),
            "placement": level.get("placement"),
        },
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

            records = get_all_records(user_id)

            cleaned_records = [
                clean_record(record)
                for record in records
            ]

            completed = [
                record
                for record in cleaned_records
                if (
                    record["percent"] == 100
                    and record["status"] == "accepted"
                )
            ]

            players[expected_name] = {
                "id": user_id,
                "username": profile.get("username"),
                "placement": profile.get("placement"),
                "points": (
                    float(profile["points"])
                    if profile.get("points") is not None
                    else None
                ),
                "country": profile.get("country"),
                "badge": profile.get("badge"),
                "is_banned": profile.get("is_banned"),

                "records": cleaned_records,

                "completed_levels": completed,
            }

            print(
                f"  OK | "
                f"#{profile.get('placement')} | "
                f"{profile.get('points')} points | "
                f"{len(completed)} completed levels"
            )

        except Exception as error:

            print(
                f"  ERROR: {error}"
            )

            players[expected_name] = {
                "id": user_id,
                "username": expected_name,
                "placement": None,
                "points": None,
                "country": None,
                "badge": None,
                "is_banned": None,
                "records": [],
                "completed_levels": [],
                "error": str(error),
            }

        # Avoid hammering the API.
        time.sleep(0.2)

    output = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "players": players,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"Finished! Updated {len(players)} players."
    )

    print(
        f"Saved to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
