#!/usr/bin/env python3
"""Fetch Kalshi PGA markets (free public API)."""

import requests
import csv
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

SERIES = [
    "KXPGAROUNDSCORE",
    "KXPGAWIN",
    "KXPGATOP5",
    "KXPGATOP10",
    "KXPGATOP20",
    "KXPGAR1LEAD",
    "KXPGAR2LEAD",
    "KXPGAR3LEAD",
    "KXPGAMAKECUT",
    "KXPGAH2H",
    "KXPGABIRDIES",
]

OUTPUT_DIR = Path("data/kalshi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_markets(series_ticker: str, status: str = "open", limit: int = 200):
    markets = []
    cursor = None
    params = {"series_ticker": series_ticker, "status": status, "limit": limit}

    while True:
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{BASE_URL}/markets", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error fetching {series_ticker}: {e}")
            break

        batch = data.get("markets", [])
        markets.extend(batch)
        cursor = data.get("cursor")
        if not cursor or not batch:
            break
    return markets


def market_to_row(m: dict) -> dict:
    return {
        "source": "Kalshi",
        "series": m.get("event_ticker", "").split("-")[0] if m.get("event_ticker") else "",
        "ticker": m.get("ticker"),
        "event_ticker": m.get("event_ticker"),
        "title": m.get("title") or m.get("yes_sub_title") or "",
        "yes_bid": m.get("yes_bid_dollars"),
        "yes_ask": m.get("yes_ask_dollars"),
        "last_price": m.get("last_price_dollars"),
        "volume": m.get("volume_fp"),
        "open_interest": m.get("open_interest_fp"),
        "close_time": m.get("close_time"),
        "status": m.get("status"),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def save_csv(rows, path: Path):
    if not rows:
        print(f"  No data → {path}")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows → {path}")


def main():
    print("Fetching Kalshi...")
    all_rows = []
    for series in SERIES:
        markets = fetch_markets(series)
        rows = [market_to_row(m) for m in markets]
        all_rows.extend(rows)
        save_csv(rows, OUTPUT_DIR / f"{series.lower()}.csv")

    save_csv(all_rows, OUTPUT_DIR / "all_kalshi.csv")
    print(f"Kalshi done. Total: {len(all_rows):,}")


if __name__ == "__main__":
    main()
