#!/usr/bin/env python3
"""Fetch PrizePicks golf props (works with or without API key)."""

import os
import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "prizepicks"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GOLF_LEAGUES = [
    {"id": 1, "name": "PGA"},
    {"id": 256, "name": "LPGA"},
    {"id": 228, "name": "LIVGOLF"},
    {"id": 131, "name": "EUROGOLF"},
]

API_KEY = os.getenv("PRIZEPICKS_API_KEY")  # optional


def fetch_league(league):
    url = f"https://partner-api.prizepicks.com/projections?league_id={league['id']}&single_stat=true"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Only add Authorization if a key is present
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 429:
                import time
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  {league['name']} error (attempt {attempt+1}): {e}")
    return None


def main():
    print("Fetching PrizePicks...")
    all_rows = []

    for league in GOLF_LEAGUES:
        print(f"  {league['name']}...")
        data = fetch_league(league)
        if not data or "data" not in data:
            print(f"  → No data for {league['name']}")
            continue

        included = data.get("included", [])
        player_map = {}
        team_map = {}

        for item in included:
            if item.get("type") == "new_player":
                player_map[item["id"]] = item.get("attributes", {})
            elif item.get("type") == "team":
                team_map[item["id"]] = item.get("attributes", {})

        for proj in data["data"]:
            attrs = proj.get("attributes", {})
            rels = proj.get("relationships", {})

            player_id = rels.get("new_player", {}).get("data", {}).get("id")
            player = player_map.get(player_id, {})
            team_id = player.get("team_id")
            team = team_map.get(team_id, {})

            row = {
                "source": "PrizePicks",
                "league": league["name"],
                "player_id": player_id,
                "player_name": player.get("name"),
                "position": player.get("position"),
                "team": team.get("abbreviation") or team.get("team_name"),
                "stat_type": attrs.get("stat_type"),
                "line_score": attrs.get("line_score"),
                "adjusted_odds": attrs.get("adjusted_odds"),
                "odds_type": attrs.get("odds_type"),
                "status": attrs.get("status"),
                "start_time": attrs.get("start_time"),
                "data_id": proj.get("id"),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
            all_rows.append(row)

    if all_rows:
        path = OUTPUT_DIR / "prizepicks_golf.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"PrizePicks done. Wrote {len(all_rows):,} rows → {path}")
    else:
        print("PrizePicks: no data returned")


if __name__ == "__main__":
    main()
