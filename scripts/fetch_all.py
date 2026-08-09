#!/usr/bin/env python3
"""Run all fetchers."""

from fetch_kalshi import main as kalshi_main
from fetch_prizepicks import main as pp_main
from fetch_underdog import main as ud_main

if __name__ == "__main__":
    print("=== Starting full props pull ===\n")
    kalshi_main()
    print()
    pp_main()
    print()
    ud_main()
    print("\n=== All done ===")
