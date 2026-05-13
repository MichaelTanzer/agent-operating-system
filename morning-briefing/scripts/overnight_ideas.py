#!/usr/bin/env python3
"""
overnight_ideas.py - Weekday Overnight Ideas MVP.

Generates four grouped idea buckets for MT's Morning Briefing System. Phase 1 is
intentionally local and read-only except for optional runtime-only idea history
recording on live runs.

Dry-run:
    python3 morning-briefing/scripts/overnight_ideas.py --dry-run
    python3 morning-briefing/scripts/overnight_ideas.py --dry-run --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


HISTORY_FILENAME = "idea_history.jsonl"
IDEAS_PER_BUCKET = 3


@dataclass(frozen=True)
class Bucket:
    bucket_id: str
    label: str
    ideas: tuple[str, ...]


BUCKETS: tuple[Bucket, ...] = (
    Bucket(
        bucket_id="kanban_good_to_great",
        label="Kanban good -> great",
        ideas=(
            "Audit the five oldest ready beads and write the single decision or artifact that would let an agent start each one today. Use the result to draft one reusable acceptance-criteria pattern, without creating or moving any tasks.",
            "Pick one recently completed bead and reconstruct where the agent had to infer MT's taste, risk tolerance, or definition of done. Turn that into a sharper task-spec prompt that would have reduced ambiguity before implementation began.",
            "Review blocked or slow-moving beads for a repeated dependency such as credentials, domain context, missing examples, or unclear review owner. Propose one lightweight preflight check that would catch that dependency during decomposition.",
            "Compare a clean bead chain with a messy one and name the smallest structural difference that changed agent throughput. Convert that difference into a rubric MT can apply before launching another swarm.",
            "Scan the current board for tasks that are really research questions wearing implementation clothing. Rewrite one as a decision memo prompt and one as an implementation bead so the boundary is visible.",
            "Find a bead where fatherhood-level time scarcity would make the next action too vague to start in a ten-minute window. Reframe it as a tiny prompt with inputs, stop condition, and a visible artifact.",
        ),
    ),
    Bucket(
        bucket_id="extend_mt_capabilities",
        label="Extend MT's capabilities",
        ideas=(
            "Design a TanzerBot prompt that forces every company note to separate observable evidence, valuation implication, and the analyst's private hunch. Test it on one watchlist company where the narrative feels seductive but the causal mechanism is still thin.",
            "Draft a psychoanalytic self-review prompt for investment research that asks where certainty may be defending against ambiguity. Pair the answer with one disconfirming data source so the exercise changes the research plan, not just the mood.",
            "Create a ceramics-looking exercise for knowledge work: choose one research artifact and ask what its foot, wall, glaze, and firing flaw would be. Translate those metaphors into concrete edits to the artifact's structure, evidence, prose, and review process.",
            "Build a one-page fatherhood operating note that identifies which recurring decisions should be made once, templated, or delegated to an agent. Keep the output practical by requiring one calendar change, one checklist, and one thing to stop doing.",
            "Write an art-history comparison prompt that places a company thesis beside a painting, asking what is foreground, background, patronage, restoration, and missing provenance. Use the answers to expose which parts of the thesis are evidence and which are composition.",
            "Formulate a philosophy-and-economics reading question that links agency, incentives, and attention in MT's current work system. The deliverable should be one paragraph and one experiment that could be tried this week.",
        ),
    ),
    Bucket(
        bucket_id="coding_stack_efficacy",
        label="Coding stack efficacy",
        ideas=(
            "Instrument one agent workflow with a before-and-after trace: prompt, files touched, tests run, human interventions, and final defect. Use the trace to identify whether the bottleneck is model reasoning, repo context, tool permissioning, or task framing.",
            "Choose a repeated coding task and specify the smallest evaluation that would prove an agent can do it without MT watching. Include fixture data, expected diff shape, and one failure mode that should block automatic acceptance.",
            "Sketch a routing rule for when Codex, Claude, Gemini, or a smaller local script should own a task in the stack. Anchor the rule in observable task features such as repo size, test availability, visual verification, and need for long-context synthesis.",
            "Take one brittle shell workflow and turn it into a stdlib Python check with explicit exit codes and terse diagnostics. The goal is not abstraction, but making the next agent failure cheaper to understand.",
            "Review the last substantial code change for places where tests verified syntax but not user-visible behavior. Add a prompt template that asks future agents to name the behavioral invariant before they touch files.",
            "Map the agent architecture as queues, workers, memory, evaluators, and human approval gates rather than as product names. Then mark the one edge where latency, cost, or silent failure most likely damages MT's morning flow.",
        ),
    ),
    Bucket(
        bucket_id="new_project_ideas",
        label="New project ideas",
        ideas=(
            "Prototype a TanzerBot 'thesis kiln' that takes a rough investment idea through stages named wedge, evidence, counterfire, valuation, and memo. Each stage should produce a visible artifact and reject the idea if it cannot survive a specific test.",
            "Build a small art-history recommender for investment research craft that pairs one company situation with a painting, patron, or movement. The output should teach a research habit such as looking for provenance, workshop authorship, restoration, or market fashion.",
            "Create a fatherhood-and-focus dashboard that turns the next week into protected deep-work blocks, family constraints, and agent-delegable chores. It should produce only calendar suggestions and checklists, not automatic calendar mutations.",
            "Make a psychoanalytic reading companion that logs recurring metaphors, defenses, and unresolved questions across notes without treating them as diagnoses. Its first use case should be improving the honesty of research memos and postmortems.",
            "Design an economics-of-attention ledger that prices meetings, agent runs, research rabbit holes, and maintenance tasks in scarce morning energy. The MVP should show one weekly reallocation that buys back a meaningful block of creative work.",
            "Prototype a ceramics collection notebook that connects object photos, maker history, clay body, glaze, and auction provenance. Add a companion prompt that asks what each object teaches about taste formation and investment judgment.",
        ),
    ),
)


def idea_id(bucket_id: str, idea: str) -> str:
    digest = hashlib.sha256(f"{bucket_id}\0{idea}".encode("utf-8")).hexdigest()
    return digest[:16]


def sentence_count(text: str) -> int:
    return sum(1 for chunk in text.split(".") if chunk.strip())


def state_dir() -> Path:
    if configured := os.environ.get("MORNING_STATE_DIR"):
        return Path(configured).expanduser()
    hermes_home = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    return hermes_home / "morning"


def history_path(runtime_state_dir: Path | None = None) -> Path:
    return (runtime_state_dir or state_dir()) / HISTORY_FILENAME


def load_history(path: Path) -> set[str]:
    """Read previously emitted idea ids from local runtime history, if present."""
    if not path.exists():
        return set()

    seen: set[str] = set()
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ids = record.get("idea_ids", [])
                if isinstance(ids, list):
                    seen.update(str(item) for item in ids)
    except OSError:
        return set()
    return seen


def select_ideas(bucket: Bucket, seen_ids: set[str]) -> list[str]:
    fresh = [
        idea for idea in bucket.ideas
        if idea_id(bucket.bucket_id, idea) not in seen_ids
    ]
    selected = fresh[:IDEAS_PER_BUCKET]
    if len(selected) < IDEAS_PER_BUCKET:
        for idea in bucket.ideas:
            if idea not in selected:
                selected.append(idea)
            if len(selected) == IDEAS_PER_BUCKET:
                break
    return selected


def build_payload(
    *,
    dry_run: bool,
    seen_ids: set[str] | None = None,
    generated_at: datetime | None = None,
) -> dict:
    emitted_at = generated_at or datetime.now(timezone.utc)
    seen = seen_ids or set()
    buckets = []

    for bucket in BUCKETS:
        ideas = select_ideas(bucket, seen)
        buckets.append({
            "id": bucket.bucket_id,
            "label": bucket.label,
            "ideas": ideas,
        })

    return {
        "job": "overnight_ideas",
        "generated_at": emitted_at.isoformat(),
        "dry_run": dry_run,
        "auto_task_creation": False,
        "gbrain_writes": False,
        "buckets": buckets,
    }


def iter_idea_ids(payload: dict) -> Iterable[str]:
    for bucket in payload["buckets"]:
        for idea in bucket["ideas"]:
            yield idea_id(bucket["id"], idea)


def append_history(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "generated_at": payload["generated_at"],
        "bucket_ids": [bucket["id"] for bucket in payload["buckets"]],
        "idea_ids": list(iter_idea_ids(payload)),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def render_plain(payload: dict) -> str:
    lines = []
    if payload["dry_run"]:
        lines.append("[DRY RUN] overnight_ideas.py")
    lines.append("Overnight Ideas")
    lines.append("Auto task creation: off | Gbrain writes: off")

    for bucket in payload["buckets"]:
        lines.append("")
        lines.append(bucket["label"])
        for idea in bucket["ideas"]:
            lines.append(f"- {idea}")

    return "\n".join(lines)


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    if len(payload.get("buckets", [])) != 4:
        errors.append("expected exactly 4 buckets")
    for bucket in payload.get("buckets", []):
        ideas = bucket.get("ideas", [])
        if len(ideas) != IDEAS_PER_BUCKET:
            errors.append(f"{bucket.get('id', '<unknown>')} expected 3 ideas")
        for idea in ideas:
            if sentence_count(idea) != 2:
                errors.append(f"{bucket.get('id', '<unknown>')} idea is not 2 sentences: {idea}")
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekday overnight ideas")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing runtime state")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of grouped bullets")
    parser.add_argument(
        "--state-dir",
        type=Path,
        help="Override runtime state directory for idea_history.jsonl",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime_state_dir = args.state_dir.expanduser() if args.state_dir else state_dir()
    runtime_history_path = history_path(runtime_state_dir)
    seen_ids = load_history(runtime_history_path)
    payload = build_payload(dry_run=args.dry_run, seen_ids=seen_ids)
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
            print(f"WARNING: could not write idea history: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
