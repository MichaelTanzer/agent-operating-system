#!/usr/bin/env python3
"""Build read-only Kanban cleanup proposals from the collector snapshot.

Dry-run:
    python3 morning-briefing/scripts/kanban_cleanup.py --dry-run

This script recommends cleanup candidates only. It never mutates Kanban boards.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from kanban_brief import (
    DEFAULT_ARCHIVE_AFTER_DAYS,
    collect_kanban,
    default_db_path,
    default_state_path,
)


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower().strip(), right.lower().strip()).ratio()


def flatten_tasks(collector_payload: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for board in collector_payload.get("boards", []):
        for task in board.get("tasks", []):
            item = dict(task)
            item["board"] = board.get("board")
            tasks.append(item)
    return tasks


def epoch_from_iso(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(time.mktime(time.strptime(value, "%Y-%m-%dT%H:%M:%SZ")))
    except ValueError:
        return None


def cleanup_payload(
    collector_payload: dict[str, Any],
    now: int | None = None,
    idle_days: int = 7,
    archive_after_days: int = DEFAULT_ARCHIVE_AFTER_DAYS,
    duplicate_threshold: float = 0.85,
) -> dict[str, Any]:
    now_ts = int(now if now is not None else time.time())
    tasks = flatten_tasks(collector_payload)
    by_id = {task["id"]: task for task in tasks}

    stale_tasks = []
    oversized_tasks = []
    orphaned_chains = []
    archivable_items = []
    duplicate_candidates = []

    for task in tasks:
        created = epoch_from_iso(task.get("created_at")) or 0
        started = epoch_from_iso(task.get("started_at")) or created
        completed = epoch_from_iso(task.get("completed_at"))
        children = task.get("dependencies", {}).get("children", [])
        parents = task.get("dependencies", {}).get("parents", [])

        if task.get("status") not in {"done", "archived"} and now_ts - max(started, created) > idle_days * 86400:
            stale_tasks.append({
                "id": task["id"],
                "title": task["title"],
                "status": task["status"],
                "assignee": task.get("assignee"),
                "idle_days": int((now_ts - max(started, created)) // 86400),
                "recommendation": "review, unblock, or archive if obsolete",
            })

        if len(children) > 3:
            oversized_tasks.append({
                "id": task["id"],
                "title": task["title"],
                "child_count": len(children),
                "children": children,
                "recommendation": "consider splitting into explicit phase cards or marking the parent done",
            })

        if task.get("status") == "todo" and parents:
            parent_statuses = [by_id.get(parent_id, {}).get("status") for parent_id in parents]
            if parent_statuses and all(status == "done" for status in parent_statuses):
                orphaned_chains.append({
                    "id": task["id"],
                    "title": task["title"],
                    "parents": parents,
                    "recommendation": "parent chain is complete; verify dispatcher should promote this child",
                })

        if task.get("status") == "done" and completed and now_ts - completed > archive_after_days * 86400 and not children:
            archivable_items.append({
                "id": task["id"],
                "title": task["title"],
                "completed_at": task.get("completed_at"),
                "recommendation": "safe archive candidate if no external audit need remains",
            })

    open_tasks = [task for task in tasks if task.get("status") not in {"done", "archived"}]
    for i, left in enumerate(open_tasks):
        for right in open_tasks[i + 1 :]:
            score = title_similarity(left.get("title", ""), right.get("title", ""))
            if score >= duplicate_threshold:
                duplicate_candidates.append({
                    "left_id": left["id"],
                    "left_title": left["title"],
                    "right_id": right["id"],
                    "right_title": right["title"],
                    "similarity": round(score, 3),
                    "recommendation": "compare bodies and merge/archive one if they represent the same work",
                })

    return {
        "job": "kanban_cleanup_proposal",
        "generated_at": collector_payload.get("generated_at"),
        "dry_run_safe": True,
        "kanban_mutations": False,
        "source_collector_version": collector_payload.get("collector_version"),
        "summary": {
            "stale_tasks": len(stale_tasks),
            "duplicate_candidates": len(duplicate_candidates),
            "oversized_tasks": len(oversized_tasks),
            "wrong_profile_assignments": 0,
            "orphaned_chains": len(orphaned_chains),
            "archivable_items": len(archivable_items),
        },
        "stale_tasks": stale_tasks,
        "duplicate_candidates": duplicate_candidates,
        "oversized_tasks": oversized_tasks,
        "wrong_profile_assignments": [],
        "orphaned_chains": orphaned_chains,
        "archivable_items": archivable_items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Kanban cleanup proposal builder")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON recommendations without mutations")
    parser.add_argument("--db-path", default=str(default_db_path()))
    parser.add_argument("--state-path", default=str(default_state_path()))
    parser.add_argument("--now", type=int)
    parser.add_argument("--idle-days", type=int, default=7)
    parser.add_argument("--archive-after-days", type=int, default=DEFAULT_ARCHIVE_AFTER_DAYS)
    args = parser.parse_args()

    try:
        collector = collect_kanban(
            db_path=Path(args.db_path).expanduser(),
            state_path=Path(args.state_path).expanduser(),
            now=args.now,
        )
        payload = cleanup_payload(
            collector,
            now=args.now,
            idle_days=args.idle_days,
            archive_after_days=args.archive_after_days,
        )
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
