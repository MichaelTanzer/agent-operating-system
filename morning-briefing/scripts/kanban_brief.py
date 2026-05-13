#!/usr/bin/env python3
"""Collect read-only Kanban board data for MT's morning brief.

Dry-run:
    python3 morning-briefing/scripts/kanban_brief.py --dry-run

The collector reads the local Hermes Kanban SQLite database and emits structured
JSON. It never mutates Kanban boards. Persisted collector state is written only
when --write-state is supplied, so dry-runs are safe in tests and dispatch runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_HEARTBEAT_STALE_SECONDS = 4 * 60 * 60
DEFAULT_ARCHIVE_AFTER_DAYS = 30
MT_SIGNAL_TERMS = (
    "needs mt",
    "mt",
    "michael",
    "human",
    "operator",
    "approval",
    "approve",
    "decision",
    "blocked",
    "clarification",
    "question",
    "unblock",
)


def utc_iso(timestamp: int | float | None) -> str | None:
    if timestamp is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(timestamp)))


def default_db_path() -> Path:
    return Path(os.environ.get("HERMES_KANBAN_DB", "~/.hermes/kanban.db")).expanduser()


def default_state_path() -> Path:
    state_dir = Path(os.environ.get("MORNING_STATE_DIR", "~/.hermes/morning")).expanduser()
    return state_dir / "kanban_collector_state.json"


def json_loads_maybe(raw: str | None, fallback: Any = None) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(query, params)]


def fetch_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    tasks = rows(conn, "SELECT * FROM tasks ORDER BY created_at ASC, id ASC")
    comments = rows(
        conn,
        """
        SELECT id, task_id, author, body, created_at
        FROM task_comments
        ORDER BY created_at ASC, id ASC
        """,
    )
    events = rows(
        conn,
        """
        SELECT id, task_id, run_id, kind, payload, created_at
        FROM task_events
        ORDER BY created_at ASC, id ASC
        """,
    )
    links = rows(conn, "SELECT parent_id, child_id FROM task_links ORDER BY parent_id, child_id")
    runs = rows(
        conn,
        """
        SELECT id, task_id, profile, step_key, status, claim_lock, claim_expires,
               worker_pid, max_runtime_seconds, last_heartbeat_at, started_at,
               ended_at, outcome, summary, metadata, error
        FROM task_runs
        ORDER BY started_at ASC, id ASC
        """,
    )
    return {"tasks": tasks, "comments": comments, "events": events, "links": links, "runs": runs}


def brief_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task["id"],
        "title": task["title"],
        "status": task["status"],
        "assignee": task.get("assignee"),
        "tenant": task.get("tenant"),
        "priority": task.get("priority"),
        "created_at": utc_iso(task.get("created_at")),
        "started_at": utc_iso(task.get("started_at")),
        "completed_at": utc_iso(task.get("completed_at")),
        "current_run_id": task.get("current_run_id"),
        "consecutive_failures": task.get("consecutive_failures") or 0,
    }


def latest_by_task(items: list[dict[str, Any]], limit: int = 3) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in sorted(items, key=lambda row: (row.get("created_at") or 0, row.get("id") or 0), reverse=True):
        task_id = item.get("task_id")
        if task_id and len(grouped[task_id]) < limit:
            grouped[task_id].append(item)
    return grouped


def comment_summary(comment: dict[str, Any]) -> dict[str, Any]:
    body = str(comment.get("body") or "")
    return {
        "id": comment.get("id"),
        "author": comment.get("author"),
        "created_at": utc_iso(comment.get("created_at")),
        "body": body[:500],
    }


def event_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = json_loads_maybe(event.get("payload"), event.get("payload"))
    return {
        "id": event.get("id"),
        "kind": event.get("kind"),
        "run_id": event.get("run_id"),
        "created_at": utc_iso(event.get("created_at")),
        "payload": payload,
    }


def task_has_mt_signal(task: dict[str, Any], comments: list[dict[str, Any]], events: list[dict[str, Any]]) -> bool:
    if task.get("status") == "blocked":
        return True
    haystacks = [task.get("title") or "", task.get("body") or ""]
    haystacks.extend(str(comment.get("body") or "") for comment in comments)
    for event in events:
        if event.get("kind") in {"blocked", "unblocked"}:
            return True
        haystacks.append(str(event.get("payload") or ""))
    combined = "\n".join(haystacks).lower()
    return any(term in combined for term in MT_SIGNAL_TERMS)


def build_dependencies(links: list[dict[str, Any]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    parents: dict[str, list[str]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)
    for link in links:
        parent = link["parent_id"]
        child = link["child_id"]
        parents[child].append(parent)
        children[parent].append(child)
    return parents, children


def classify_stale(task: dict[str, Any], now: int, heartbeat_stale_seconds: int) -> tuple[list[str], dict[str, Any]]:
    reasons: list[str] = []
    detail: dict[str, Any] = {}

    claim_expires = task.get("claim_expires")
    if claim_expires and int(claim_expires) < now and task.get("status") in {"running", "claimed"}:
        reasons.append("claim_expired")
        detail["claim_expires"] = utc_iso(claim_expires)

    if task.get("status") in {"running", "claimed"}:
        last_heartbeat = task.get("last_heartbeat_at") or task.get("started_at")
        if last_heartbeat and now - int(last_heartbeat) > heartbeat_stale_seconds:
            reasons.append("heartbeat_stale")
            detail["last_heartbeat_at"] = utc_iso(task.get("last_heartbeat_at"))
            detail["heartbeat_age_seconds"] = now - int(last_heartbeat)

        max_runtime = task.get("max_runtime_seconds")
        started_at = task.get("started_at")
        if max_runtime and started_at and now - int(started_at) > 2 * int(max_runtime):
            reasons.append("running_over_2x_max_runtime")
            detail["runtime_seconds"] = now - int(started_at)
            detail["max_runtime_seconds"] = int(max_runtime)

    if (task.get("consecutive_failures") or 0) >= 2:
        reasons.append("multiple_consecutive_failures")
        detail["consecutive_failures"] = task.get("consecutive_failures")

    return reasons, detail


def build_board_payload(
    board_key: str,
    tasks: list[dict[str, Any]],
    comments_by_task: dict[str, list[dict[str, Any]]],
    events_by_task: dict[str, list[dict[str, Any]]],
    runs_by_task: dict[str, list[dict[str, Any]]],
    parents_by_task: dict[str, list[str]],
    children_by_task: dict[str, list[str]],
    since_ts: int,
    now: int,
    heartbeat_stale_seconds: int,
) -> dict[str, Any]:
    counts = Counter(task["status"] for task in tasks)
    blocked: list[dict[str, Any]] = []
    running: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    completed_since_last_run: list[dict[str, Any]] = []
    needs_mt: list[dict[str, Any]] = []
    task_records: list[dict[str, Any]] = []

    for task in tasks:
        task_id = task["id"]
        task_comments = comments_by_task.get(task_id, [])
        task_events = events_by_task.get(task_id, [])
        dependencies = {
            "parents": sorted(parents_by_task.get(task_id, [])),
            "children": sorted(children_by_task.get(task_id, [])),
        }
        record = {
            **brief_task(task),
            "dependencies": dependencies,
            "latest_comments": [comment_summary(comment) for comment in task_comments],
            "latest_events": [event_summary(event) for event in task_events],
            "latest_runs": [
                {
                    "id": run.get("id"),
                    "profile": run.get("profile"),
                    "status": run.get("status"),
                    "outcome": run.get("outcome"),
                    "started_at": utc_iso(run.get("started_at")),
                    "ended_at": utc_iso(run.get("ended_at")),
                    "summary": run.get("summary"),
                    "error": run.get("error"),
                }
                for run in runs_by_task.get(task_id, [])[:3]
            ],
        }
        task_records.append(record)

        if task.get("status") == "blocked":
            blocked.append(record)
        if task.get("status") in {"running", "claimed"} or task.get("claim_lock"):
            running.append(record)

        reasons, detail = classify_stale(task, now, heartbeat_stale_seconds)
        if reasons:
            stale.append({**brief_task(task), "reasons": reasons, **detail})

        if task.get("completed_at") and int(task["completed_at"]) > since_ts:
            completed_since_last_run.append(record)

        if task_has_mt_signal(task, task_comments, task_events):
            signals = []
            if task.get("status") == "blocked":
                signals.append("status=blocked")
            for comment in task_comments:
                body = str(comment.get("body") or "").lower()
                if any(term in body for term in MT_SIGNAL_TERMS):
                    signals.append(f"comment:{comment.get('id')}")
            for event in task_events:
                if event.get("kind") in {"blocked", "unblocked"}:
                    signals.append(f"event:{event.get('kind')}:{event.get('id')}")
            needs_mt.append({**brief_task(task), "signals": sorted(set(signals)) or ["text_match"]})

    return {
        "board": board_key,
        "counts_by_status": dict(sorted(counts.items())),
        "total_tasks": len(tasks),
        "blocked_tasks": blocked,
        "running_or_claimed_tasks": running,
        "stale_heartbeats_or_claims": stale,
        "completed_since_last_run": completed_since_last_run,
        "tasks_needing_mt": needs_mt,
        "tasks": task_records,
    }


def collect_kanban(
    db_path: Path,
    state_path: Path,
    now: int | None = None,
    heartbeat_stale_seconds: int = DEFAULT_HEARTBEAT_STALE_SECONDS,
) -> dict[str, Any]:
    now_ts = int(now if now is not None else time.time())
    state = load_state(state_path)
    since_ts = int(state.get("last_run_at") or 0)

    if not db_path.exists():
        raise FileNotFoundError(f"Kanban database not found: {db_path}")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        snapshot = fetch_snapshot(conn)
    finally:
        conn.close()

    comments_by_task = latest_by_task(snapshot["comments"], limit=3)
    events_by_task = latest_by_task(snapshot["events"], limit=5)
    runs_by_task = latest_by_task(snapshot["runs"], limit=5)
    parents_by_task, children_by_task = build_dependencies(snapshot["links"])

    boards: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in snapshot["tasks"]:
        board_key = task.get("tenant") or "default"
        boards[board_key].append(task)

    board_payloads = [
        build_board_payload(
            board_key=board_key,
            tasks=board_tasks,
            comments_by_task=comments_by_task,
            events_by_task=events_by_task,
            runs_by_task=runs_by_task,
            parents_by_task=parents_by_task,
            children_by_task=children_by_task,
            since_ts=since_ts,
            now=now_ts,
            heartbeat_stale_seconds=heartbeat_stale_seconds,
        )
        for board_key, board_tasks in sorted(boards.items())
    ]

    status_totals: Counter[str] = Counter()
    for board in board_payloads:
        status_totals.update(board["counts_by_status"])

    next_state = {
        "last_run_at": now_ts,
        "last_run_at_iso": utc_iso(now_ts),
        "last_seen_task_count": len(snapshot["tasks"]),
        "last_seen_event_id": max((event.get("id") or 0 for event in snapshot["events"]), default=0),
        "last_seen_comment_id": max((comment.get("id") or 0 for comment in snapshot["comments"]), default=0),
    }

    return {
        "job": "kanban_morning_brief",
        "collector_version": 1,
        "generated_at": utc_iso(now_ts),
        "dry_run_safe": True,
        "kanban_mutations": False,
        "db_path": str(db_path),
        "state_path": str(state_path),
        "since_last_run": {
            "previous_last_run_at": utc_iso(since_ts) if since_ts else None,
            "previous_last_run_epoch": since_ts or None,
        },
        "summary": {
            "boards": len(board_payloads),
            "tasks": len(snapshot["tasks"]),
            "counts_by_status": dict(sorted(status_totals.items())),
            "blocked_tasks": sum(len(board["blocked_tasks"]) for board in board_payloads),
            "running_or_claimed_tasks": sum(len(board["running_or_claimed_tasks"]) for board in board_payloads),
            "stale_heartbeats_or_claims": sum(len(board["stale_heartbeats_or_claims"]) for board in board_payloads),
            "completed_since_last_run": sum(len(board["completed_since_last_run"]) for board in board_payloads),
            "tasks_needing_mt": sum(len(board["tasks_needing_mt"]) for board in board_payloads),
        },
        "boards": board_payloads,
        "state_update": next_state,
    }


def count_text(counts: dict[str, int]) -> str:
    ordered_statuses = ("triage", "todo", "ready", "running", "blocked", "done", "archived")
    parts = [f"{status} {counts[status]}" for status in ordered_statuses if counts.get(status)]
    parts.extend(f"{status} {count}" for status, count in sorted(counts.items()) if status not in ordered_statuses and count)
    return ", ".join(parts) if parts else "0 tasks"


def task_line(task: dict[str, Any], *, include_reason: bool = False) -> str:
    assignee = task.get("assignee") or "unassigned"
    status = task.get("status") or "unknown"
    title = str(task.get("title") or "").strip()
    bits = [f"{task['id']} ({status}, {assignee})"]
    if title:
        bits.append(title)
    if include_reason:
        reasons = task.get("reasons") or task.get("signals") or []
        if reasons:
            bits.append("; ".join(str(reason) for reason in reasons[:3]))
    return " — ".join(bits)


def top_tasks(tasks: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(tasks, key=lambda task: (-(task.get("priority") or 0), task.get("created_at") or "", task.get("id") or ""))[:limit]


def gather_stuck_or_risky(board: dict[str, Any]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for task in board.get("blocked_tasks", []):
        by_id[task["id"]] = {**task, "reasons": ["blocked"]}
    for task in board.get("stale_heartbeats_or_claims", []):
        existing = by_id.get(task["id"], {})
        reasons = list(dict.fromkeys([*(existing.get("reasons") or []), *(task.get("reasons") or [])]))
        by_id[task["id"]] = {**existing, **task, "reasons": reasons}
    for task in board.get("running_or_claimed_tasks", []):
        if (task.get("consecutive_failures") or 0) >= 2:
            existing = by_id.get(task["id"], {})
            reasons = list(dict.fromkeys([*(existing.get("reasons") or []), "recent_failures"]))
            by_id[task["id"]] = {**task, **existing, "reasons": reasons}
    return list(by_id.values())


def suggested_actions(payload: dict[str, Any], needs_mt: list[dict[str, Any]], stuck: list[dict[str, Any]], completed: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    if needs_mt:
        actions.append(f"Answer or route Needs MT item {needs_mt[0]['id']} before spawning more work.")
    if stuck:
        actions.append(f"Inspect stuck/risky task {stuck[0]['id']} and either unblock, restart, or archive after review.")
    ready_count = payload.get("summary", {}).get("counts_by_status", {}).get("ready", 0)
    if ready_count:
        actions.append(f"Pick the highest-leverage ready task from the {ready_count} ready backlog items.")
    if completed:
        actions.append(f"Review completion {completed[0]['id']} for downstream follow-up; create follow-up cards only if MT approves.")
    actions.append("Keep recommendations read-only this morning; do not mutate Kanban automatically.")
    actions.append("Confirm every running task still has a clear next checkpoint and owner.")
    actions.append("If the brief feels noisy, tighten assignee/profile routing rather than dumping the task list.")
    return actions[:5]


def render_morning_brief(payload: dict[str, Any]) -> str:
    """Render a compact, recommend-only weekday Kanban morning brief.

    The renderer consumes the structured collector payload produced by
    collect_kanban(). It does not read or write Kanban state itself.
    """
    boards = payload.get("boards", [])
    needs_mt: list[dict[str, Any]] = []
    stuck: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    for board in boards:
        needs_mt.extend(
            task
            for task in board.get("tasks_needing_mt", [])
            if task.get("status") not in {"done", "archived"}
        )
        stuck.extend(gather_stuck_or_risky(board))
        completed.extend(board.get("completed_since_last_run", []))

    needs_mt = top_tasks(needs_mt, 5)
    stuck = top_tasks(stuck, 5)
    completed = sorted(completed, key=lambda task: task.get("completed_at") or "", reverse=True)[:5]
    actions = suggested_actions(payload, needs_mt, stuck, completed)

    lines = [
        "Kanban Morning Brief",
        f"Generated: {payload.get('generated_at') or 'unknown'} — recommend only; no Kanban mutations.",
        "",
        "Backlog",
    ]
    for board in boards:
        lines.append(f"- {board.get('board')}: {board.get('total_tasks', 0)} total; {count_text(board.get('counts_by_status', {}))}")

    lines.extend(["", "Needs MT"])
    if needs_mt:
        lines.extend(f"- {task_line(task, include_reason=True)}" for task in needs_mt)
    else:
        lines.append("- None flagged.")

    lines.extend(["", "Stuck / risky"])
    if stuck:
        lines.extend(f"- {task_line(task, include_reason=True)}" for task in stuck)
    else:
        lines.append("- No blocked, stale, or risky running tasks flagged.")

    lines.extend(["", "Completed since last run"])
    if completed:
        lines.extend(f"- {task_line(task)}" for task in completed)
    else:
        lines.append("- None recorded in the collector window.")

    lines.extend(["", "Suggested actions"])
    lines.extend(f"{idx}. {action}" for idx, action in enumerate(actions, start=1))
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Kanban board collector and morning brief renderer")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing collector state")
    parser.add_argument("--write-state", action="store_true", help="Persist since-last-run state after collecting")
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output raw collector JSON or compact morning brief text")
    parser.add_argument("--db-path", default=str(default_db_path()), help="Path to Hermes Kanban SQLite DB")
    parser.add_argument("--state-path", default=str(default_state_path()), help="Path for collector state JSON")
    parser.add_argument("--now", type=int, help="Override current epoch seconds for deterministic tests")
    parser.add_argument("--heartbeat-stale-seconds", type=int, default=DEFAULT_HEARTBEAT_STALE_SECONDS)
    args = parser.parse_args()

    try:
        payload = collect_kanban(
            db_path=Path(args.db_path).expanduser(),
            state_path=Path(args.state_path).expanduser(),
            now=args.now,
            heartbeat_stale_seconds=args.heartbeat_stale_seconds,
        )
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.write_state and not args.dry_run:
        save_state(Path(args.state_path).expanduser(), payload["state_update"])
        payload["state_written"] = True
    else:
        payload["state_written"] = False

    if args.format == "text":
        print(render_morning_brief(payload), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
