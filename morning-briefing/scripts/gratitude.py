#!/usr/bin/env python3
"""Emit MT's daily gratitude prompt.

This is a no-agent job: it performs no network calls, reads no secrets, and
prints one deterministic message for the delivery layer to send separately.

Dry-run:
    python3 morning-briefing/scripts/gratitude.py --dry-run

Verification JSON:
    python3 morning-briefing/scripts/gratitude.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any


JOB_NAME = "gratitude"
EXPECTED_POINTS = 3
PROMPT_TEXT = (
    "MT, what are three things you're grateful for today?\n\n"
    "Please reply with three short points:\n"
    "1.\n"
    "2.\n"
    "3."
)


@dataclass(frozen=True)
class ConfigCheck:
    """Small, secret-free summary of the optional config validation."""

    checked: bool
    valid: bool
    warning: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "checked": self.checked,
            "valid": self.valid,
        }
        if self.warning:
            result["warning"] = self.warning
        return result


def check_config() -> ConfigCheck:
    """Validate the source-controlled job contract when config_loader is usable.

    This deliberately returns warnings instead of failing the job. The prompt is
    important enough to send even if optional local config dependencies are
    absent or the repo is being exercised in a stripped-down environment.
    """

    try:
        from config_loader import _jobs_yaml_path, _load_yaml, get_job
    except ImportError:
        return ConfigCheck(
            checked=False,
            valid=True,
            warning="config_loader unavailable; using built-in prompt contract",
        )
    except SystemExit:
        return ConfigCheck(
            checked=False,
            valid=True,
            warning="config_loader dependency unavailable; using built-in prompt contract",
        )

    try:
        jobs_config = _load_yaml(_jobs_yaml_path())
        job = get_job({"jobs": jobs_config.get("jobs", {})}, JOB_NAME)
    except (AttributeError, FileNotFoundError, KeyError, SystemExit):
        return ConfigCheck(
            checked=False,
            valid=True,
            warning="gratitude job config unavailable; using built-in prompt contract",
        )

    contract = job.get("output_contract", {})
    problems: list[str] = []

    if not job.get("enabled", True):
        problems.append("job disabled")
    if job.get("implementation") != "script":
        problems.append("implementation is not script")
    if contract.get("format") != "prompt_message":
        problems.append("output format is not prompt_message")
    if contract.get("text") != "What are three things you're grateful for?":
        problems.append("prompt text contract changed")
    if contract.get("expects_response") is not True:
        problems.append("expects_response is not true")

    if problems:
        return ConfigCheck(
            checked=True,
            valid=False,
            warning="; ".join(problems),
        )

    return ConfigCheck(checked=True, valid=True)


def build_payload(*, dry_run: bool, config_check: ConfigCheck) -> dict[str, Any]:
    return {
        "job": JOB_NAME,
        "dry_run": dry_run,
        "status": "ready",
        "delivery": {
            "mode": "separate_interactive_message",
            "expects_response": True,
        },
        "message": {
            "text": PROMPT_TEXT,
            "expected_response_points": EXPECTED_POINTS,
        },
        "config": config_check.as_dict(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily gratitude prompt job")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be sent without invoking delivery",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print deterministic verification output as JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config_check = check_config()

    if args.json:
        payload = build_payload(dry_run=args.dry_run, config_check=config_check)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.dry_run:
        print("[DRY RUN] gratitude.py")
        print("Would send a separate interactive message:")
        print(PROMPT_TEXT)
        if config_check.warning:
            print(f"Config warning: {config_check.warning}", file=sys.stderr)
        return 0

    print(PROMPT_TEXT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
