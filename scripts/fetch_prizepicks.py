#!/usr/bin/env python3
"""Fetch PrizePicks golf props with better debugging."""

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

def fetch_league(league):
    url = f"https://partner-api.prizepicks.com/projections?league_id={league['id']}&single_stat=true"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://app.prizepicks.com/",
        "Origin": "https://app.prizepicks.com"
    }

    try:
        r = requests.get(url, headers=headers, timeout=30)
        print(f"  {league['name']} → Status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"  Response text: {r.text[:300]}")
            return None
            
        data = r.json()
        
        # Debug: show top-level keys
        print(f"  Keys in response: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        
        return data
        
    except Exception as e:
        print(f"  {league['name']} error: {e}")
        return None


def main():
    print("Fetching PrizePicks...")
    all_rows = []

    for league in GOLF_LEAGUES:
        print(f"\n{league['name']}:")
        data = fetch_league(league)
        
        if not data:
            continue
            
        if "data" not in data:
            print(f"  → No 'data' key found")
            continue

        projections = data.get("data", [])
        included = data.get("included", [])
        
        print(f"  → Found {len(projections)} projections")

        player_map = {}
        team_map = {}

        for item in included:
            if item.get("type") == "new_player":
                player_map[item["id"]] = item.get("attributes", {})
            elif item.get("type") == "team":
                team_map[item["id"]] = item.get("attributes", {})

        for proj in projections:
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
        print(f"\nPrizePicks done. Wrote {len(all_rows):,} rows → {path}")
    else:
        print("\nPrizePicks: no data returned")


if __name__ == "__main__":
    main()
