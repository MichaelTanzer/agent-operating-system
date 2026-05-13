#!/usr/bin/env python3
"""
no_do.py - One daily anti-priority for MT's Morning Briefing System.

Phase 1 is intentionally local and side-effect free: no Kanban mutations and no
Gbrain writes. If external context is unavailable, the job emits the deterministic
fallback recommendation below.

Dry-run: python morning-briefing/scripts/no_do.py --dry-run
JSON:    python morning-briefing/scripts/no_do.py --json
"""
import argparse
import json
import sys

LABEL = "One Thing to Not Do Today"
SOURCE = "deterministic_phase1_fallback"
RECOMMENDATION = (
    "Do not turn today's task into a new architecture, broader scope, or fresh "
    "abstraction; finish the smallest accepted slice."
)


def build_payload(dry_run=False):
    return {
        "label": LABEL,
        "recommendation": RECOMMENDATION,
        "dry_run": dry_run,
        "source": SOURCE,
        "recommend_only": True,
        "kanban_mutations": False,
        "gbrain_writes": False,
    }


def format_plain(payload):
    prefix = "[DRY RUN] " if payload["dry_run"] else ""
    return f"{prefix}{payload['label']}: {payload['recommendation']}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="One Thing to Not Do Today job")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    payload = build_payload(dry_run=args.dry_run)
    if args.json_output:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(format_plain(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
