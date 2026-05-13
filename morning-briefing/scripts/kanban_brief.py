#!/usr/bin/env python3
"""kanban_brief.py — Phase 2 placeholder. Dry-run: python morning-briefing/scripts/kanban_brief.py --dry-run"""
import argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print("[DRY RUN] kanban_brief.py — Phase 2 agent implementation pending")
        sys.exit(0)
    print("ERROR: not yet implemented.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
