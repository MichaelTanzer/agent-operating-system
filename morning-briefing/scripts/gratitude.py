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
from datetime import UTC, datetime
from pathlib import Path
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
DEFAULT_GBRAIN_ROOT = "~/dev/repos/brain"
CAPTURE_POLICY_NOT_APPROVED = "not_approved"


@dataclass(frozen=True)
class ResponseCapturePolicy:
    """Consent and policy gate for optional gratitude reply persistence."""

    enabled: bool
    consent_required: bool
    policy_decision: str
    policy_path: str
    gbrain_collection: str | None = None
    gbrain_page: str | None = None

    @property
    def policy_approved(self) -> bool:
        return self.policy_decision == "approved"

    @property
    def target_configured(self) -> bool:
        return (
            self.enabled
            and self.consent_required
            and self.policy_approved
            and bool(self.gbrain_collection)
            and bool(self.gbrain_page)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "consent_required": self.consent_required,
            "policy_decision": self.policy_decision,
            "policy_path": self.policy_path,
            "gbrain_collection": self.gbrain_collection,
            "gbrain_page": self.gbrain_page,
            "capture_target_configured": self.target_configured,
            "gbrain_writes": False,
        }


def default_response_capture_policy() -> ResponseCapturePolicy:
    return ResponseCapturePolicy(
        enabled=False,
        consent_required=True,
        policy_decision=CAPTURE_POLICY_NOT_APPROVED,
        policy_path="policies/GBRAIN_POLICY.md",
        gbrain_collection="personal/gratitude",
        gbrain_page="personal/gratitude/replies.md",
    )


def response_capture_policy_from_job(job: dict[str, Any] | None) -> ResponseCapturePolicy:
    if not job:
        return default_response_capture_policy()

    capture = job.get("response_capture") or {}
    if not isinstance(capture, dict):
        return default_response_capture_policy()

    default = default_response_capture_policy()
    return ResponseCapturePolicy(
        enabled=bool(capture.get("enabled", default.enabled)),
        consent_required=bool(capture.get("consent_required", default.consent_required)),
        policy_decision=str(capture.get("policy_decision", default.policy_decision)),
        policy_path=str(capture.get("policy_path", default.policy_path)),
        gbrain_collection=capture.get("gbrain_collection", default.gbrain_collection),
        gbrain_page=capture.get("gbrain_page", default.gbrain_page),
    )


@dataclass(frozen=True)
class ConfigCheck:
    """Small, secret-free summary of the optional config validation."""

    checked: bool
    valid: bool
    warning: str | None = None
    response_capture: ResponseCapturePolicy = default_response_capture_policy()

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "checked": self.checked,
            "valid": self.valid,
        }
        if self.warning:
            result["warning"] = self.warning
        result["response_capture"] = self.response_capture.as_dict()
        return result


def check_config() -> ConfigCheck:
    """Validate the source-controlled job contract when config_loader is usable.

    This deliberately returns warnings instead of failing the job. The prompt is
    important enough to send even if optional local config dependencies are
    absent or the repo is being exercised in a stripped-down environment.
    """

    try:
        from config_loader import get_job, load_config
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
        job = get_job(load_config(), JOB_NAME)
    except (AttributeError, FileNotFoundError, KeyError, SystemExit):
        return ConfigCheck(
            checked=False,
            valid=True,
            warning="gratitude job config unavailable; using built-in prompt contract",
        )

    response_capture = response_capture_policy_from_job(job)
    contract = job.get("output_contract", {})
    problems: list[str] = []

    if not job.get("enabled", True):
        problems.append("job disabled")
    if job.get("implementation") != "script":
        problems.append("implementation is not script")
    if contract.get("format") != "prompt_message":
        problems.append("output format is not prompt_message")
    if contract.get("text") != PROMPT_TEXT:
        problems.append("prompt text contract does not match script output")
    if contract.get("expects_response") is not True:
        problems.append("expects_response is not true")
    if response_capture.enabled and not response_capture.policy_approved:
        problems.append("response capture enabled before Gbrain policy approval")
    if response_capture.policy_approved and not response_capture.consent_required:
        problems.append("approved response capture must still require explicit consent")

    if problems:
        return ConfigCheck(
            checked=True,
            valid=False,
            warning="; ".join(problems),
            response_capture=response_capture,
        )

    return ConfigCheck(checked=True, valid=True, response_capture=response_capture)


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
        "response_capture": config_check.response_capture.as_dict(),
    }


def capture_gratitude_reply(
    *,
    reply_text: str,
    consent_granted: bool,
    policy: ResponseCapturePolicy,
    gbrain_root: str = DEFAULT_GBRAIN_ROOT,
) -> dict[str, Any]:
    """Persist a gratitude reply only when every consent/policy gate is open.

    The returned status deliberately omits the reply text so logs and cron output
    do not leak the private response.
    """
    if not policy.enabled:
        return {"status": "skipped", "reason": "capture_disabled", "gbrain_writes": False}
    if not policy.policy_approved:
        return {"status": "skipped", "reason": "policy_not_approved", "gbrain_writes": False}
    if policy.consent_required and not consent_granted:
        return {"status": "skipped", "reason": "consent_not_granted", "gbrain_writes": False}
    if not policy.gbrain_page:
        return {"status": "skipped", "reason": "gbrain_page_missing", "gbrain_writes": False}

    root = Path(gbrain_root).expanduser()
    if not root.exists():
        return {"status": "skipped", "reason": "gbrain_unavailable", "gbrain_writes": False}

    page = root / policy.gbrain_page
    try:
        page.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).date().isoformat()
        entry = (
            f"\n## {stamp}\n\n"
            f"policy: {policy.policy_path}\n"
            "consent: explicit\n\n"
            f"{reply_text.strip()}\n"
        )
        with page.open("a", encoding="utf-8") as handle:
            handle.write(entry)
    except OSError as exc:
        return {
            "status": "skipped",
            "reason": "gbrain_write_failed",
            "error": exc.__class__.__name__,
            "gbrain_writes": False,
        }

    return {
        "status": "captured",
        "reason": None,
        "gbrain_writes": True,
        "gbrain_page": policy.gbrain_page,
        "policy_path": policy.policy_path,
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
    parser.add_argument(
        "--capture-reply",
        metavar="TEXT",
        help="Attempt consent/policy-gated Gbrain capture of a gratitude reply",
    )
    parser.add_argument(
        "--consent-granted",
        action="store_true",
        help="Mark the supplied reply as explicitly approved for capture",
    )
    parser.add_argument(
        "--gbrain-root",
        default=DEFAULT_GBRAIN_ROOT,
        help="Brain content repo root for approved capture attempts",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config_check = check_config()

    if args.capture_reply is not None:
        result = capture_gratitude_reply(
            reply_text=args.capture_reply,
            consent_granted=args.consent_granted,
            policy=config_check.response_capture,
            gbrain_root=args.gbrain_root,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

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
