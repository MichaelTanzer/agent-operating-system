#!/usr/bin/env python3
"""Build read-only Kanban cleanup proposals from the collector snapshot.

Dry-run:
    python3 morning-briefing/scripts/kanban_cleanup.py --dry-run

This script recommends cleanup candidates only. It never mutates Kanban boards.
The output is intentionally approval-ready: a human can review the proposed
cleanup actions and then choose which Kanban mutations, if any, to perform.
"""

from __future__ import annotations

import argparse
import json
import re
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

OPEN_STATUSES = {"todo", "ready", "running", "claimed", "blocked", "triage"}
CLOSED_STATUSES = {"done", "archived"}
ACCEPTANCE_TERMS = (
    "acceptance",
    "done when",
    "definition of done",
    "test plan",
    "verification",
    "success criteria",
)
VAGUE_TERMS = (
    "tbd",
    "todo",
    "misc",
    "cleanup",
    "clean up",
    "improve",
    "fix things",
    "figure out",
    "look into",
    "explore",
    "research",
    "investigate",
)
IDEA_TERMS = (
    "idea:",
    "ideas:",
    "brainstorm",
    "someday",
    "parking lot",
    "would be nice",
    "maybe we should",
    "non-actionable",
)
PROFILE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("reviewer", ("review pr", "pr review", "code review", "review pull request", "audit pr")),
    ("researcher", ("research", "source", "market", "scan", "taxonomy", "investigate")),
    ("writer", ("write", "draft", "essay", "brief", "memo", "proposal", "copy")),
    ("devops", ("deploy", "cron", "ci", "workflow", "monitor", "alert", "infra")),
    ("coder", ("implement", "build", "script", "test", "bug", "fix", "refactor", "api")),
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


def text_for(task: dict[str, Any]) -> str:
    parts = [task.get("title") or "", task.get("body") or ""]
    for comment in task.get("latest_comments", []):
        parts.append(str(comment.get("body") or ""))
    return "\n".join(parts).strip()


def compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def body_has_acceptance(task: dict[str, Any]) -> bool:
    body = str(task.get("body") or "").lower()
    return any(term in body for term in ACCEPTANCE_TERMS)


def body_word_count(task: dict[str, Any]) -> int:
    return len(re.findall(r"\b\w+\b", str(task.get("body") or "")))


def expected_profile(task: dict[str, Any]) -> str | None:
    haystack = text_for(task).lower()
    for profile, terms in PROFILE_RULES:
        if any(term in haystack for term in terms):
            return profile
    return None


def recommendation(task: dict[str, Any], action: str, reason: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    item = {
        "id": task["id"],
        "title": task["title"],
        "status": task.get("status"),
        "assignee": task.get("assignee"),
        "board": task.get("board"),
        "reason": reason,
        "recommended_action": action,
    }
    if extra:
        item.update(extra)
    return item


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
    wrong_profile_assignments = []
    missing_acceptance_criteria = []
    vague_tasks_needing_rewrite = []
    non_actionable_ideas_for_gbrain = []

    for task in tasks:
        status = task.get("status")
        created = epoch_from_iso(task.get("created_at")) or 0
        started = epoch_from_iso(task.get("started_at")) or created
        completed = epoch_from_iso(task.get("completed_at"))
        children = task.get("dependencies", {}).get("children", [])
        parents = task.get("dependencies", {}).get("parents", [])
        task_text = text_for(task)
        task_text_lower = task_text.lower()
        open_task = status in OPEN_STATUSES

        if status not in CLOSED_STATUSES and now_ts - max(started, created) > idle_days * 86400:
            stale_tasks.append(recommendation(
                task,
                "review, unblock, re-scope, or archive if obsolete",
                f"open for {int((now_ts - max(started, created)) // 86400)} idle days",
                {"idle_days": int((now_ts - max(started, created)) // 86400)},
            ))

        if len(children) > 3:
            oversized_tasks.append(recommendation(
                task,
                "split into explicit phase cards or mark parent done if it only tracks completed children",
                "task has more than three child dependencies",
                {"child_count": len(children), "children": children},
            ))

        if status == "todo" and parents:
            parent_statuses = [by_id.get(parent_id, {}).get("status") for parent_id in parents]
            if parent_statuses and all(parent_status == "done" for parent_status in parent_statuses):
                orphaned_chains.append(recommendation(
                    task,
                    "verify dispatcher promotion or manually promote after approval",
                    "task is still todo even though all known parents are done",
                    {"parents": parents},
                ))

        if status == "done" and completed and now_ts - completed > archive_after_days * 86400 and not children:
            archivable_items.append(recommendation(
                task,
                "archive after human approval if no external audit need remains",
                f"done for more than {archive_after_days} days and has no children",
                {"completed_at": task.get("completed_at")},
            ))

        if open_task and not body_has_acceptance(task):
            missing_acceptance_criteria.append(recommendation(
                task,
                "rewrite with explicit acceptance criteria before dispatch",
                "body does not contain acceptance, verification, test plan, or success criteria language",
                {"body_word_count": body_word_count(task)},
            ))

        if open_task and (
            any(term in task_text_lower for term in VAGUE_TERMS)
            or body_word_count(task) < 8
            or len(str(task.get("title") or "")) < 12
        ):
            vague_tasks_needing_rewrite.append(recommendation(
                task,
                "rewrite into a concrete executable card with scope, artifact, owner, and acceptance criteria",
                "task text is short or contains vague planning terms",
                {"body_preview": compact_whitespace(str(task.get("body") or ""))[:180]},
            ))

        if open_task and any(term in task_text_lower for term in IDEA_TERMS):
            non_actionable_ideas_for_gbrain.append(recommendation(
                task,
                "move the idea to Gbrain and close/archive the Kanban card after approval unless it becomes executable work",
                "task reads like an idea parking-lot item rather than actionable work",
                {"gbrain_namespace_hint": "ideas/"},
            ))

        expected = expected_profile(task)
        current_assignee = task.get("assignee")
        if open_task and expected and current_assignee and current_assignee not in {expected, "default"}:
            wrong_profile_assignments.append(recommendation(
                task,
                f"reassign to {expected} or confirm current specialist is intentional",
                f"text matches {expected} profile but assignee is {current_assignee}",
                {"suggested_assignee": expected},
            ))
        elif open_task and expected and current_assignee == "default" and expected in {"reviewer", "researcher", "writer", "devops"}:
            wrong_profile_assignments.append(recommendation(
                task,
                f"consider assigning to {expected} instead of default",
                f"text matches {expected} profile and default may be too generic",
                {"suggested_assignee": expected},
            ))

    open_tasks = [task for task in tasks if task.get("status") not in CLOSED_STATUSES]
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
                    "recommended_action": "compare bodies and merge/archive one if they represent the same work",
                })

    sections = {
        "stale_tasks": stale_tasks,
        "duplicate_candidates": duplicate_candidates,
        "oversized_tasks": oversized_tasks,
        "wrong_profile_assignments": wrong_profile_assignments,
        "orphaned_chains": orphaned_chains,
        "archivable_items": archivable_items,
        "missing_acceptance_criteria": missing_acceptance_criteria,
        "vague_tasks_needing_rewrite": vague_tasks_needing_rewrite,
        "non_actionable_ideas_for_gbrain": non_actionable_ideas_for_gbrain,
    }
    total_recommendations = sum(len(items) for items in sections.values())

    return {
        "job": "kanban_cleanup_proposal",
        "proposal_status": "approval_ready",
        "generated_at": collector_payload.get("generated_at"),
        "dry_run_safe": True,
        "kanban_mutations": False,
        "no_changes_made": True,
        "safety_notice": "No Kanban changes were made. This is a recommend-only cleanup proposal that requires human approval before any mutation.",
        "source_collector_version": collector_payload.get("collector_version"),
        "summary": {
            "total_recommendations": total_recommendations,
            "stale_tasks": len(stale_tasks),
            "duplicate_candidates": len(duplicate_candidates),
            "oversized_tasks": len(oversized_tasks),
            "wrong_profile_assignments": len(wrong_profile_assignments),
            "orphaned_chains": len(orphaned_chains),
            "archivable_items": len(archivable_items),
            "missing_acceptance_criteria": len(missing_acceptance_criteria),
            "vague_tasks_needing_rewrite": len(vague_tasks_needing_rewrite),
            "non_actionable_ideas_for_gbrain": len(non_actionable_ideas_for_gbrain),
        },
        "approval_instructions": [
            "Review each recommendation and approve, reject, or modify it.",
            "Apply approved Kanban mutations manually or with a separate explicitly approved cleanup task.",
            "Move non-actionable ideas to Gbrain before closing/archive decisions when useful.",
        ],
        **sections,
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
