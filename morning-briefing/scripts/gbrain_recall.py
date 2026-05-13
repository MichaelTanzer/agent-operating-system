#!/usr/bin/env python3
"""
gbrain_recall.py - Weekday Gbrain Recall MVP.

Surfaces one read-only Gbrain note that has not been recalled recently. Runtime
recall history is tracked only in ~/.hermes/morning/last_run/gbrain_recall.json
(or --state-dir), never in Gbrain. If Gbrain is unavailable, the job still emits
one transparent fallback note grounded in repo conventions and MT profile domains.

Dry-run:
    python3 morning-briefing/scripts/gbrain_recall.py --dry-run
    python3 morning-briefing/scripts/gbrain_recall.py --dry-run --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

JOB = "gbrain_recall"
RECENCY_EXCLUSION_DAYS = 14
STATE_RELATIVE_PATH = Path("last_run") / "gbrain_recall.json"
LIST_LIMIT = 80

DOMAIN_QUERIES = (
    "TanzerBot investment research craft AI agent architectures",
    "psychoanalysis ceramics art history philosophy economics fatherhood",
    "morning briefing agent operating system guardrails scope creep",
)

FALLBACK_NOTES: tuple[dict[str, str], ...] = (
    {
        "id": "fallback-research-craft-agent-architecture",
        "origin_date": "2026-05-13",
        "title": "Fallback: research craft needs agent-operating discipline",
        "summary": (
            "When Gbrain is unreachable, keep the morning recall useful by returning to MT's standing domains: "
            "investment research craft, TanzerBot, AI agents, psychoanalysis, ceramics, art history, philosophy/economics, and fatherhood."
        ),
        "source": "repo conventions/profile domains fallback",
    },
    {
        "id": "fallback-smallest-accepted-slice",
        "origin_date": "2026-05-13",
        "title": "Fallback: smallest accepted slice before architecture",
        "summary": (
            "The recurring operating guardrail is to finish the named file, test, PR, or decision before turning the work into a broader architecture."
        ),
        "source": "repo conventions/profile domains fallback",
    },
)


@dataclass(frozen=True)
class Candidate:
    note_id: str
    slug: str
    title: str
    origin_date: str
    summary: str
    source: str
    score: int = 0


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def state_dir() -> Path:
    if configured := os.environ.get("MORNING_STATE_DIR"):
        return Path(configured).expanduser()
    hermes_home = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    return hermes_home / "morning"


def state_path(runtime_state_dir: Path | None = None) -> Path:
    return (runtime_state_dir or state_dir()) / STATE_RELATIVE_PATH


def load_history(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {"recalled": {}}
    recalled = payload.get("recalled") if isinstance(payload, dict) else None
    return {"recalled": recalled if isinstance(recalled, dict) else {}}


def write_history(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def note_id_for(slug: str, title: str) -> str:
    return hashlib.sha256(f"{slug}\0{title}".encode("utf-8")).hexdigest()[:16]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def recalled_recently(note_id: str, history: dict[str, Any], *, today: date, days: int = RECENCY_EXCLUSION_DAYS) -> bool:
    recalled = history.get("recalled", {}) if isinstance(history, dict) else {}
    raw = recalled.get(note_id) if isinstance(recalled, dict) else None
    last = parse_date(raw if isinstance(raw, str) else None)
    if last is None:
        return False
    return today - last < timedelta(days=days)


def record_recall(history: dict[str, Any], candidate: Candidate, *, today: date) -> dict[str, Any]:
    recalled = history.get("recalled", {}) if isinstance(history, dict) else {}
    if not isinstance(recalled, dict):
        recalled = {}
    recalled[candidate.note_id] = today.isoformat()
    return {
        "job": JOB,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "recency_exclusion_days": RECENCY_EXCLUSION_DAYS,
        "last_note_id": candidate.note_id,
        "last_slug": candidate.slug,
        "recalled": recalled,
    }


def clean_cli_lines(output: str) -> list[str]:
    lines = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[ai.gateway]"):
            continue
        if stripped.lower() in {"no results.", "no results"}:
            continue
        lines.append(stripped)
    return lines


def run_gbrain(args: list[str], *, timeout: int = 5) -> tuple[int, str, str]:
    env = os.environ.copy()
    db_url_path = Path("~/.gbrain/database_url").expanduser()
    if "GBRAIN_DATABASE_URL" not in env:
        try:
            db_url = db_url_path.read_text(encoding="utf-8").strip()
        except OSError:
            db_url = ""
        if db_url:
            env["GBRAIN_DATABASE_URL"] = db_url
    try:
        completed = subprocess.run(
            ["gbrain", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout, completed.stderr


def parse_gbrain_listing(output: str, *, score: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    for line in clean_cli_lines(output):
        # Current gbrain list/search output is tab-separated: slug, type, date, title.
        parts = line.split("\t")
        if len(parts) >= 4:
            slug, _kind, origin, title = parts[0], parts[1], parts[2], "\t".join(parts[3:])
        elif len(parts) >= 2:
            slug, title = parts[0], parts[-1]
            origin = "unknown"
        else:
            continue
        if not slug or slug.lower().startswith("warning"):
            continue
        candidates.append(
            Candidate(
                note_id=note_id_for(slug, title),
                slug=slug,
                title=title.strip() or slug,
                origin_date=origin[:10] if origin else "unknown",
                summary="",
                source="gbrain",
                score=score,
            )
        )
    return candidates


def first_nonempty_paragraph(text: str, max_chars: int = 260) -> str:
    lines = clean_cli_lines(text)
    if not lines:
        return "No page body was returned; title recalled from Gbrain index."

    body_lines: list[str] = []
    in_frontmatter = False
    for line in lines:
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        # Skip common title/metadata echoes so the recall feels like a note, not
        # a raw page dump.
        if stripped.startswith("#"):
            continue
        if re.match(r"^(type|title|tags|created|updated):\s", stripped, flags=re.IGNORECASE):
            continue
        body_lines.append(stripped)

    body = " ".join(body_lines or lines)
    body = re.sub(r"\s+", " ", body).strip()
    if not body:
        return "No page body was returned; title recalled from Gbrain index."
    if len(body) <= max_chars:
        return body
    truncated = body[:max_chars].rsplit(" ", 1)[0]
    return truncated.rstrip(".,;:") + "…"


def hydrate_candidate(candidate: Candidate) -> Candidate:
    rc, stdout, _stderr = run_gbrain(["get", candidate.slug], timeout=5)
    if rc != 0 or not stdout.strip():
        return candidate
    return Candidate(
        note_id=candidate.note_id,
        slug=candidate.slug,
        title=candidate.title,
        origin_date=candidate.origin_date,
        summary=first_nonempty_paragraph(stdout),
        source=candidate.source,
        score=candidate.score,
    )


def dedupe_candidates(candidates: Iterable[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    unique: list[Candidate] = []
    for candidate in candidates:
        if candidate.note_id in seen:
            continue
        seen.add(candidate.note_id)
        unique.append(candidate)
    return unique


def collect_gbrain_candidates() -> tuple[list[Candidate], str | None]:
    collected: list[Candidate] = []
    last_error: str | None = None

    for rank, query in enumerate(DOMAIN_QUERIES):
        rc, stdout, stderr = run_gbrain(["search", query], timeout=5)
        if rc == 0:
            collected.extend(parse_gbrain_listing(stdout, score=100 - rank))
        else:
            last_error = stderr.strip() or f"gbrain search exited {rc}"

    # Keyword search may return nothing even when the brain has pages. Fall back
    # to the page index so the MVP can still recall a real local note.
    if not collected:
        rc, stdout, stderr = run_gbrain(["list", "-n", str(LIST_LIMIT)], timeout=5)
        if rc == 0:
            collected.extend(parse_gbrain_listing(stdout, score=10))
        else:
            last_error = stderr.strip() or f"gbrain list exited {rc}"

    return dedupe_candidates(collected), last_error


def fallback_candidates() -> list[Candidate]:
    return [
        Candidate(
            note_id=item["id"],
            slug=item["id"],
            title=item["title"],
            origin_date=item["origin_date"],
            summary=item["summary"],
            source=item["source"],
            score=0,
        )
        for item in FALLBACK_NOTES
    ]


def choose_candidate(candidates: list[Candidate], history: dict[str, Any], *, today: date) -> Candidate:
    ordered = sorted(candidates, key=lambda item: item.score, reverse=True)
    for candidate in ordered:
        if not recalled_recently(candidate.note_id, history, today=today):
            return hydrate_candidate(candidate) if candidate.source == "gbrain" else candidate
    # If every note is recent, repeat the highest scoring candidate rather than failing.
    selected = ordered[0]
    return hydrate_candidate(selected) if selected.source == "gbrain" else selected


def build_payload(
    *,
    dry_run: bool,
    history: dict[str, Any] | None = None,
    today: date | None = None,
    candidates: list[Candidate] | None = None,
    gbrain_error: str | None = None,
) -> dict[str, Any]:
    run_date = today or today_utc()
    history = history or {"recalled": {}}

    source_status = "gbrain"
    if candidates is None:
        candidates, gbrain_error = collect_gbrain_candidates()
    if not candidates:
        candidates = fallback_candidates()
        source_status = "fallback"
    elif all(candidate.source != "gbrain" for candidate in candidates):
        source_status = "fallback"

    selected = choose_candidate(candidates, history, today=run_date)
    recently_recalled = recalled_recently(selected.note_id, history, today=run_date)

    return {
        "job": JOB,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "gbrain_writes": False,
        "history_writes": not dry_run,
        "recency_exclusion_days": RECENCY_EXCLUSION_DAYS,
        "source_status": source_status,
        "gbrain_error": gbrain_error if source_status == "fallback" else None,
        "note": {
            "id": selected.note_id,
            "slug": selected.slug,
            "title": selected.title,
            "origin_date": selected.origin_date or "unknown",
            "summary": selected.summary or "No body summary available; recall selected from the Gbrain page index.",
            "source": selected.source,
            "recalled_within_exclusion_window": recently_recalled,
        },
    }


def render_plain(payload: dict[str, Any]) -> str:
    prefix = "[DRY RUN] " if payload["dry_run"] else ""
    note = payload["note"]
    lines = [
        f"{prefix}Gbrain Recall",
        f"Origin date: {note['origin_date']} | Source: {note['source']}",
        f"Recall: {note['title']}",
        f"Why it matters: {note['summary']}",
    ]
    if payload["source_status"] == "fallback":
        lines.append("Gbrain read unavailable or empty; using transparent read-only fallback.")
    return "\n".join(lines)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    note = payload.get("note", {})
    if payload.get("gbrain_writes") is not False:
        errors.append("gbrain_writes must be false")
    if not note.get("origin_date"):
        errors.append("origin date is required")
    plain_lines = [line for line in render_plain(payload).splitlines() if line.strip()]
    if len(plain_lines) > 5:
        errors.append("plain output must be 3-5 lines")
    if len(plain_lines) < 3:
        errors.append("plain output must be at least 3 lines")
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Surface one read-only Gbrain recall note")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing recall history")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of 3-5 plain text lines")
    parser.add_argument("--state-dir", type=Path, help="Override runtime state directory for last_run/gbrain_recall.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime_state_dir = args.state_dir.expanduser() if args.state_dir else state_dir()
    runtime_state_path = state_path(runtime_state_dir)
    history = load_history(runtime_state_path)
    payload = build_payload(dry_run=args.dry_run, history=history)
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_plain(payload))

    if not args.dry_run:
        note = payload["note"]
        candidate = Candidate(
            note_id=note["id"],
            slug=note["slug"],
            title=note["title"],
            origin_date=note["origin_date"],
            summary=note["summary"],
            source=note["source"],
        )
        try:
            write_history(runtime_state_path, record_recall(history, candidate, today=today_utc()))
        except OSError as exc:
            print(f"WARNING: could not write recall history: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
