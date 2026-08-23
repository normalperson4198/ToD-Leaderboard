import json
import requests
from pathlib import Path
from datetime import datetime, timezone

API_URL = "PUT_THE_GLOBAL_DEMONLIST_ENDPOINT_HERE"

PLAYERS_FILE = Path("players.txt")
OUTPUT_FILE = Path("data/players.json")


def load_players():
    return [
        name.strip()
        for name in PLAYERS_FILE.read_text(encoding="utf-8").splitlines()
        if name.strip()
    ]


def get_player(name):
    response = requests.get(
        API_URL,
        params={"name": name},
        timeout=20
    )

    response.raise_for_status()
    return response.json()


def main():
    players = load_players()
    result = {}

    for name in players:
        try:
            data = get_player(name)

            result[name] = {
                "flag": data["flag"],
                "points": data["points"]
            }

            print(f"Found: {name}")

        except Exception as e:
            print(f"Failed: {name}: {e}")

            result[name] = {
                "flag": None,
                "points": None
            }

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "players": result
    }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
