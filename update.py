import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


API_URL = "https://demonlist.org/api/user/getCache"

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


def get_player(user_id):
    response = requests.get(
        API_URL,
        params={"id": user_id},
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if result.get("message") != "success":
        raise RuntimeError(
            f"API returned unexpected response: {result}"
        )

    return result["data"]


def main():
    players = {}

    for expected_name, user_id in PLAYERS.items():

        print(f"Fetching {expected_name} ({user_id})...")

        try:
            data = get_player(user_id)

            players[expected_name] = {
                "id": user_id,
                "username": data.get("username"),
                "placement": data.get("placement"),
                "points": data.get("points"),
                "country": data.get("country"),
                "badge": data.get("badge"),
                "is_banned": data.get("is_banned"),
            }

            print(
                f"  {data.get('username')} | "
                f"{data.get('points')} points | "
                f"{data.get('country')}"
            )

        except Exception as error:
            print(f"  ERROR: {error}")

            players[expected_name] = {
                "id": user_id,
                "username": expected_name,
                "placement": None,
                "points": None,
                "country": None,
                "badge": None,
                "is_banned": None,
                "error": str(error),
            }

        # Small delay between requests.
        time.sleep(0.2)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "players": players,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(f"Updated {len(players)} players.")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
