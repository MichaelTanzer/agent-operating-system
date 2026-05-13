#!/usr/bin/env python3
"""
cross_domain_analogy.py - Weekly Cross-Domain Analogy Prompt job.

Generates a 2-3 paragraph essay seed or short letter for MT by forcing two of
MT's standing domains into structural contact. The job is read-only with respect
to Gbrain and Kanban. It can consume a context JSON export from Gbrain/runtime
collectors when available, then degrades to deterministic local domain-pair
rotation in ~/.hermes/morning.

Dry-run:
    python3 morning-briefing/scripts/cross_domain_analogy.py --dry-run
    python3 morning-briefing/scripts/cross_domain_analogy.py --dry-run --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


HISTORY_FILENAME = "analogy_history.jsonl"
JOB_NAME = "cross_domain_analogy"
QUALITY_BAR = "structural analogy, not a generic inspirational riff"
DOMAINS: tuple[str, ...] = (
    "investment research craft",
    "AI agent architectures",
    "psychoanalytic theory",
    "ceramics",
    "art history",
    "philosophy and economics",
    "fatherhood",
    "TanzerBot",
)

DOMAIN_FRAMES: dict[str, dict[str, str]] = {
    "investment research craft": {
        "object": "a company thesis",
        "operation": "separating observed evidence from valuation implication",
        "failure": "letting a persuasive narrative outrun the mechanism that would make it true",
        "discipline": "returning to unit economics, incentives, and disconfirming facts",
    },
    "AI agent architectures": {
        "object": "an agent workflow",
        "operation": "routing context, tools, memory, review gates, and stop conditions",
        "failure": "mistaking motion across workers for verified progress",
        "discipline": "making every handoff leave an inspectable artifact",
    },
    "psychoanalytic theory": {
        "object": "a recurring pattern of attention",
        "operation": "listening for defenses, repetitions, substitutions, and belated meanings",
        "failure": "treating the presenting story as the whole causal structure",
        "discipline": "staying with resistance until the hidden bargain becomes speakable",
    },
    "ceramics": {
        "object": "a vessel on the wheel",
        "operation": "centering, opening, pulling, trimming, glazing, and firing under constraint",
        "failure": "forcing the wall after the clay has already told you where it is thin",
        "discipline": "letting pressure, moisture, timing, and touch reveal the form",
    },
    "art history": {
        "object": "a painting as an organized field of attention",
        "operation": "reading patronage, foreground, background, provenance, and restoration",
        "failure": "confusing the visible composition with the whole system that produced it",
        "discipline": "asking what the frame excludes and what later hands have repaired",
    },
    "philosophy and economics": {
        "object": "a theory of agency under scarcity",
        "operation": "linking incentives, constraints, tradeoffs, and claims about value",
        "failure": "smuggling a moral preference into what pretends to be a neutral model",
        "discipline": "making assumptions explicit enough to be argued with",
    },
    "fatherhood": {
        "object": "a day shaped by dependent life",
        "operation": "allocating attention when love, fatigue, routine, and contingency all have claims",
        "failure": "imagining control where the real task is responsiveness",
        "discipline": "building rituals sturdy enough to hold interruption without resentment",
    },
    "TanzerBot": {
        "object": "a research essay engine",
        "operation": "turning notes, models, sources, and taste into publishable judgment",
        "failure": "automating prose before the thesis has earned its pressure",
        "discipline": "forcing every claim to carry evidence, causality, and voice",
    },
}


def state_dir() -> Path:
    if configured := os.environ.get("MORNING_STATE_DIR"):
        return Path(configured).expanduser()
    hermes_home = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    return hermes_home / "morning"


def history_path(runtime_state_dir: Path | None = None) -> Path:
    return (runtime_state_dir or state_dir()) / HISTORY_FILENAME


def normalize_pair(raw: Any) -> tuple[str, str] | None:
    if isinstance(raw, dict):
        raw = raw.get("domains") or raw.get("pair") or [raw.get("domain_a"), raw.get("domain_b")]
    if not isinstance(raw, list | tuple) or len(raw) != 2:
        return None
    left, right = (str(raw[0]).strip(), str(raw[1]).strip())
    if left in DOMAINS and right in DOMAINS and left != right:
        return (left, right)
    return None


def pair_key(pair: tuple[str, str]) -> tuple[str, str]:
    return tuple(sorted(pair))  # type: ignore[return-value]


def load_history(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    pairs: list[tuple[str, str]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                pair = normalize_pair(record)
                if pair:
                    pairs.append(pair)
    except OSError:
        return []
    return pairs


def append_history(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "generated_at": payload["generated_at"],
        "domains": payload["domains"],
        "source": payload["source"],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def candidate_pairs() -> list[tuple[str, str]]:
    adjacent = [(DOMAINS[index], DOMAINS[(index + 1) % len(DOMAINS)]) for index in range(len(DOMAINS))]
    all_pairs = [
        (DOMAINS[left], DOMAINS[right])
        for left in range(len(DOMAINS))
        for right in range(left + 1, len(DOMAINS))
    ]
    merged: list[tuple[str, str]] = []
    for pair in adjacent + all_pairs:
        if pair not in merged:
            merged.append(pair)
    return merged


def context_recent_pairs(context: dict[str, Any]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for item in context.get("recent_analogies", []) if isinstance(context.get("recent_analogies", []), list) else []:
        pair = normalize_pair(item)
        if pair:
            pairs.append(pair)
    for item in context.get("avoid_pairs", []) if isinstance(context.get("avoid_pairs", []), list) else []:
        pair = normalize_pair(item)
        if pair:
            pairs.append(pair)
    return pairs


def select_domain_pair(
    *,
    state_pairs: Iterable[tuple[str, str]],
    context: dict[str, Any],
) -> tuple[str, str]:
    recent_keys = {pair_key(pair) for pair in state_pairs}
    recent_keys.update(pair_key(pair) for pair in context_recent_pairs(context))

    preferred = normalize_pair(context.get("preferred_pair"))
    if preferred and pair_key(preferred) not in recent_keys:
        return preferred

    for pair in candidate_pairs():
        if pair_key(pair) not in recent_keys:
            return pair
    return candidate_pairs()[0]


def load_context(path: Path | None, runtime_state_dir: Path | None = None) -> dict[str, Any]:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(path.expanduser())
    if env_path := os.environ.get("CROSS_DOMAIN_ANALOGY_CONTEXT_JSON"):
        candidates.append(Path(env_path).expanduser())
    base = runtime_state_dir or state_dir()
    candidates.append(base / "cross_domain_analogy_context.json")
    candidates.append(base / "gbrain_cross_domain_analogy.json")

    for candidate in candidates:
        try:
            raw = json.loads(candidate.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, dict):
            return raw
    return {}


def context_notes(context: dict[str, Any]) -> list[str]:
    raw_notes = context.get("source_notes") or context.get("notes") or []
    if not isinstance(raw_notes, list):
        return []
    return [str(note).strip() for note in raw_notes if str(note).strip()][:3]


def structural_paragraphs(pair: tuple[str, str], notes: list[str]) -> list[str]:
    left, right = pair
    a = DOMAIN_FRAMES[left]
    b = DOMAIN_FRAMES[right]
    note_sentence = f" A live note in the background: {notes[0]}" if notes else ""

    first = (
        f"Dear MT, put {left} beside {right} and the analogy is not that both reward patience; "
        f"it is that {a['object']} and {b['object']} each become trustworthy only when the maker can see the hidden load-bearing structure. "
        f"In one domain that means {a['operation']}; in the other it means {b['operation']}. "
        f"The shared craft is pressure applied through a form, not inspiration poured over empty space.{note_sentence}"
    )
    second = (
        f"The failure mode rhymes too. {left} breaks down by {a['failure']}; {right} breaks down by {b['failure']}. "
        f"So the useful question is structural: where is the artifact asking you to slow down because the surface has become more coherent than the causal joints underneath? "
        f"The answer is probably the place where a next sentence, next agent handoff, next note, or next family rhythm feels fluent but has not yet survived contact with resistance."
    )
    third = (
        f"The practical move is to borrow the discipline of one field as an instrument inside the other: {a['discipline']} while also {b['discipline']}. "
        f"That gives the opening of an essay or letter: the best systems in MT's life are not optimized for smoothness; they are built to expose the exact stress that would otherwise stay aesthetic, verbal, or automated. "
        f"A good analogy should leave a handle: one concrete test that tells whether the form is centered or merely looking centered."
    )
    return [first, second, third]


def build_payload(
    *,
    dry_run: bool,
    state_pairs: Iterable[tuple[str, str]] | None = None,
    context: dict[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    runtime_context = context or {}
    pair = select_domain_pair(state_pairs=state_pairs or [], context=runtime_context)
    notes = context_notes(runtime_context)
    source = "context" if normalize_pair(runtime_context.get("preferred_pair")) or notes else "deterministic_local_rotation"
    emitted_at = generated_at or datetime.now(timezone.utc)
    paragraphs = structural_paragraphs(pair, notes)
    return {
        "job": JOB_NAME,
        "generated_at": emitted_at.isoformat(),
        "dry_run": dry_run,
        "domains": list(pair),
        "paragraphs": paragraphs,
        "source": source,
        "quality_bar": QUALITY_BAR,
        "context_notes": notes,
        "gbrain_reads_attempted": True,
        "gbrain_writes": False,
        "kanban_mutations": False,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    domains = payload.get("domains", [])
    if not isinstance(domains, list) or len(domains) != 2:
        errors.append("expected exactly two domains")
    elif domains[0] == domains[1] or any(domain not in DOMAINS for domain in domains):
        errors.append("domains must be two distinct approved domains")
    paragraphs = payload.get("paragraphs", [])
    if not isinstance(paragraphs, list) or not 2 <= len(paragraphs) <= 3:
        errors.append("expected 2-3 paragraphs")
    else:
        for paragraph in paragraphs:
            if not isinstance(paragraph, str) or len(paragraph.split()) < 25:
                errors.append("paragraph too short for essay-seed contract")
    joined = " ".join(str(paragraph).lower() for paragraph in paragraphs)
    required_terms = ("structure", "failure", "discipline")
    if not all(term in joined for term in required_terms):
        errors.append("analogy must name structure, failure, and discipline")
    if payload.get("gbrain_writes") is not False:
        errors.append("gbrain writes must remain disabled")
    if payload.get("kanban_mutations") is not False:
        errors.append("kanban mutations must remain disabled")
    return errors


def render_plain(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    if payload["dry_run"]:
        lines.append("[DRY RUN] cross_domain_analogy.py")
    lines.append(f"Cross-Domain Analogy: {payload['domains'][0]} x {payload['domains'][1]}")
    lines.append("")
    lines.extend(payload["paragraphs"])
    return "\n\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly cross-domain analogy essay seed")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing local run history")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of plain text")
    parser.add_argument("--state-dir", type=Path, help="Override runtime state directory for analogy_history.jsonl")
    parser.add_argument("--context-json", type=Path, help="Optional Gbrain/context export JSON to prefer over local rotation")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime_state_dir = args.state_dir.expanduser() if args.state_dir else state_dir()
    runtime_history_path = history_path(runtime_state_dir)
    context = load_context(args.context_json, runtime_state_dir)
    payload = build_payload(
        dry_run=args.dry_run,
        state_pairs=load_history(runtime_history_path),
        context=context,
    )
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
        try:
            append_history(runtime_history_path, payload)
        except OSError as exc:
            print(f"WARNING: could not write analogy history: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
