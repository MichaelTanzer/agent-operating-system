#!/usr/bin/env python3
"""
no_do.py - One daily anti-priority for MT's Morning Briefing System.

The job is recommend-only. It may read derived feedback signals from Gbrain,
Kanban, or session summaries, but it does not mutate Kanban and does not write to
Gbrain during daily delivery. If durable feedback is unavailable, it emits the
stable fallback recommendation.

Dry-run: python3 morning-briefing/scripts/no_do.py --dry-run
JSON:    python3 morning-briefing/scripts/no_do.py --json
With feedback fixture:
    python3 morning-briefing/scripts/no_do.py --feedback-json signals.json --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

LABEL = "One Thing to Not Do Today"
FALLBACK_SOURCE = "deterministic_phase1_fallback"
FEEDBACK_SOURCE = "recurring_failure_mode_feedback"
FALLBACK_RECOMMENDATION = (
    "Do not turn today's task into a new architecture, broader scope, or fresh "
    "abstraction; finish the smallest accepted slice."
)

SUPPORTED_SOURCES = {"gbrain", "kanban", "session"}
SOURCE_WEIGHTS = {"gbrain": 3, "kanban": 2, "session": 2}


class FailureMode(NamedTuple):
    """Diagnostic anti-pattern that can drive the daily no-do."""

    mode_id: str
    name: str
    diagnostic: str
    recommendation: str
    keywords: tuple[str, ...]


FAILURE_MODES: tuple[FailureMode, ...] = (
    FailureMode(
        mode_id="scope_creep",
        name="Scope creep from an accepted slice",
        diagnostic="The work keeps widening after the next accepted slice is already visible.",
        recommendation=(
            "Do not expand today's accepted slice into adjacent improvements; ship or review "
            "the smallest named deliverable before adding another bead."
        ),
        keywords=("scope creep", "broader scope", "expand", "expanded", "adjacent", "oversized"),
    ),
    FailureMode(
        mode_id="architecture_as_avoidance",
        name="Architecture as avoidance",
        diagnostic="Design work is substituting for finishing the concrete implementation checkpoint.",
        recommendation=(
            "Do not turn the next concrete checkpoint into architecture work; name the file, "
            "test, or PR that proves progress and finish that first."
        ),
        keywords=("architecture", "abstraction", "framework", "redesign", "planning instead", "plan instead"),
    ),
    FailureMode(
        mode_id="premature_parallelism",
        name="Premature parallelism",
        diagnostic="More agents or branches are being added before the current checkpoint is verified.",
        recommendation=(
            "Do not spawn another lane before the active one has a verified checkpoint; close "
            "or review the current PR/task before creating more motion."
        ),
        keywords=("parallel", "spawn", "swarm", "worktree", "too many agents", "more agents"),
    ),
    FailureMode(
        mode_id="review_gate_drift",
        name="Review gate drift",
        diagnostic="The work is treated as done before the explicit review, CI, or approval gate has cleared.",
        recommendation=(
            "Do not count the work as complete until the real gate is cleared; verify CI, "
            "formal review, or MT approval before moving to the next item."
        ),
        keywords=("review required", "ci", "check failed", "blocked", "approval", "merge gate", "gitleaks"),
    ),
)


def normalize_signal(raw: dict[str, Any]) -> dict[str, str] | None:
    """Return a compact signal if it comes from an approved feedback source."""

    source = str(raw.get("source") or "").strip().lower()
    if source not in SUPPORTED_SOURCES:
        return None
    text = " ".join(
        str(raw.get(key) or "").strip()
        for key in ("title", "summary", "body", "feedback", "text", "metadata")
    ).strip()
    if not text:
        return None
    return {
        "source": source,
        "date": str(raw.get("date") or raw.get("created_at") or "").strip()[:10],
        "text": text.lower(),
    }


def load_feedback(path: Path | None) -> list[dict[str, str]]:
    """Load feedback fixture/state without making external calls.

    Runtime collectors can produce either a list of signals or a dict with a
    `signals` list. Missing files degrade to no feedback so the job still
    delivers the fallback.
    """

    if path is None:
        return []
    try:
        raw = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []
    signals = raw.get("signals", []) if isinstance(raw, dict) else raw
    if not isinstance(signals, list):
        return []
    normalized = [normalize_signal(signal) for signal in signals if isinstance(signal, dict)]
    return [signal for signal in normalized if signal]


def match_failure_modes(signals: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Score modes from recurring Gbrain/Kanban/session-derived feedback.

    A mode is eligible only when evidence is durable enough to avoid daily noise:
    at least three matching signals across at least two dates, or at least two
    source classes. Session-only feedback must cross the three-signal/two-date
    bar and cannot update the recommendation by itself from a single correction.
    """

    matches: list[dict[str, Any]] = []
    for mode in FAILURE_MODES:
        hits: list[dict[str, str]] = []
        for signal in signals:
            if any(keyword in signal["text"] for keyword in mode.keywords):
                hits.append(signal)
        if not hits:
            continue
        source_types = {hit["source"] for hit in hits}
        dates = {hit["date"] for hit in hits if hit["date"]}
        recurring_enough = len(hits) >= 3 and len(dates) >= 2
        corroborated_enough = len(source_types) >= 2 and len(hits) >= 2
        eligible = recurring_enough or corroborated_enough
        score = sum(SOURCE_WEIGHTS[hit["source"]] for hit in hits) + len(source_types) + len(dates)
        matches.append(
            {
                "mode": mode,
                "score": score,
                "eligible": eligible,
                "signal_count": len(hits),
                "source_types": sorted(source_types),
                "dates": sorted(dates),
            }
        )
    return sorted(matches, key=lambda item: (item["eligible"], item["score"]), reverse=True)


def choose_failure_mode(signals: list[dict[str, str]]) -> dict[str, Any] | None:
    for match in match_failure_modes(signals):
        if match["eligible"]:
            return match
    return None


def build_payload(dry_run: bool = False, feedback: list[dict[str, str]] | None = None) -> dict[str, Any]:
    raw_feedback = feedback or []
    normalized_feedback = [normalize_signal(signal) for signal in raw_feedback]
    feedback = [signal for signal in normalized_feedback if signal]
    selected = choose_failure_mode(feedback)
    if selected is None:
        return {
            "label": LABEL,
            "recommendation": FALLBACK_RECOMMENDATION,
            "dry_run": dry_run,
            "source": FALLBACK_SOURCE,
            "recommend_only": True,
            "kanban_mutations": False,
            "gbrain_writes": False,
            "failure_mode": "fallback_scope_architecture_abstraction",
            "evidence": {
                "eligible": False,
                "reason": "No recurring or corroborated feedback pattern met the update threshold.",
            },
        }

    mode = selected["mode"]
    return {
        "label": LABEL,
        "recommendation": mode.recommendation,
        "dry_run": dry_run,
        "source": FEEDBACK_SOURCE,
        "recommend_only": True,
        "kanban_mutations": False,
        "gbrain_writes": False,
        "failure_mode": mode.mode_id,
        "diagnostic": mode.diagnostic,
        "evidence": {
            "eligible": True,
            "signal_count": selected["signal_count"],
            "source_types": selected["source_types"],
            "dates": selected["dates"],
        },
    }


def format_plain(payload: dict[str, Any]) -> str:
    prefix = "[DRY RUN] " if payload["dry_run"] else ""
    return f"{prefix}{payload['label']}: {payload['recommendation']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One Thing to Not Do Today job")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--feedback-json",
        type=Path,
        help="Optional derived feedback fixture/state from Gbrain, Kanban, and session summaries.",
    )
    args = parser.parse_args(argv)

    payload = build_payload(dry_run=args.dry_run, feedback=load_feedback(args.feedback_json))
    if args.json_output:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(format_plain(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
