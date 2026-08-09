#!/usr/bin/env python3
"""Fetch Underdog over/under lines."""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("data/underdog")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://api.underdogfantasy.com/beta/v3/over_under_lines"


def main():
    print("Fetching Underdog...")
    try:
        r = requests.get(URL, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Underdog error: {e}")
        return

    lines = data if isinstance(data, list) else data.get("data") or data.get("over_under_lines") or []

    rows = []
    for item in lines:
        row = {
            "source": "Underdog",
            "id": item.get("id"),
            "player_id": item.get("player_id") or item.get("appearance", {}).get("player_id"),
            "stat_type": item.get("stat") or item.get("stat_type"),
            "line": item.get("line") or item.get("over_under", {}).get("line"),
            "over_odds": item.get("over_odds"),
            "under_odds": item.get("under_odds"),
            "sport_id": item.get("sport_id") or item.get("appearance", {}).get("sport_id"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        rows.append(row)

    if rows:
        path = OUTPUT_DIR / "underdog_lines.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Underdog done. Wrote {len(rows):,} rows → {path}")
    else:
        print("Underdog: no lines found")


if __name__ == "__main__":
    main()
