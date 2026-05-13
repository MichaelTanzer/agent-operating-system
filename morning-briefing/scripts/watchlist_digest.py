#!/usr/bin/env python3
"""
watchlist_digest.py — Weekday company + industry watchlist digest
Phase 2 implementation placeholder. Config scaffold phase only.

Dry-run: python morning-briefing/scripts/watchlist_digest.py --dry-run --company AON
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Watchlist digest job (agent)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--company", help="Limit to single company ticker for testing")
    args = parser.parse_args()

    if args.dry_run:
        target = f" (company={args.company})" if args.company else ""
        print(f"[DRY RUN] watchlist_digest.py{target} — Phase 2 agent implementation pending")
        sys.exit(0)

    print("ERROR: watchlist_digest.py not yet implemented for live runs.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
