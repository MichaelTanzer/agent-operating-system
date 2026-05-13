#!/usr/bin/env python3
"""
weather.py — DC weather fetch and format
Phase 2 implementation placeholder. Config scaffold phase only.

Dry-run: python morning-briefing/scripts/weather.py --dry-run
"""
import argparse
import sys

SAMPLE_OUTPUT = """DC Weather — 6:00 AM
High 78°F / Low 61°F
Partly cloudy. Umbrella: no.
AQI: 42 (Good) | Pollen: Moderate
Stroller: good to go
"""

def main():
    parser = argparse.ArgumentParser(description="DC Weather job")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] weather.py — Phase 2 implementation pending")
        print(SAMPLE_OUTPUT)
        sys.exit(0)

    # TODO Phase 2: fetch from wttr.in, AirNow, pollen source
    print("ERROR: weather.py not yet implemented for live runs.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
