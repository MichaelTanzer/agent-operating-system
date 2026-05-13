#!/usr/bin/env python3
"""
gratitude.py — Daily gratitude prompt
Sends a fixed text message. No LLM needed.

Dry-run: python morning-briefing/scripts/gratitude.py --dry-run
"""
import argparse
import sys

PROMPT_TEXT = "What are three things you're grateful for?"

def main():
    parser = argparse.ArgumentParser(description="Gratitude prompt job")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] gratitude.py")
        print(f"Would send: {PROMPT_TEXT}")
        sys.exit(0)

    # Live: print the message for the cron job to deliver via hermes
    print(PROMPT_TEXT)

if __name__ == "__main__":
    main()
