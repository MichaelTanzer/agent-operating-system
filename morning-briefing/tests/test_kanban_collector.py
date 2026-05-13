from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "morning-briefing" / "scripts" / "kanban_brief.py"
CLEANUP_SCRIPT = REPO_ROOT / "morning-briefing" / "scripts" / "kanban_cleanup.py"


def load_collector_module():
    spec = importlib.util.spec_from_file_location("kanban_brief", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT,
            assignee TEXT,
            status TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            created_by TEXT,
            created_at INTEGER NOT NULL,
            started_at INTEGER,
            completed_at INTEGER,
            workspace_kind TEXT NOT NULL DEFAULT 'scratch',
            workspace_path TEXT,
            claim_lock TEXT,
            claim_expires INTEGER,
            tenant TEXT,
            result TEXT,
            idempotency_key TEXT,
            consecutive_failures INTEGER NOT NULL DEFAULT 0,
            worker_pid INTEGER,
            last_failure_error TEXT,
            max_runtime_seconds INTEGER,
            last_heartbeat_at INTEGER,
            current_run_id INTEGER,
            workflow_template_id TEXT,
            current_step_key TEXT,
            skills TEXT,
            max_retries INTEGER
        );
        CREATE TABLE task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE task_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            run_id INTEGER,
            kind TEXT NOT NULL,
            payload TEXT,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE task_links (parent_id TEXT NOT NULL, child_id TEXT NOT NULL, PRIMARY KEY(parent_id, child_id));
        CREATE TABLE task_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            profile TEXT,
            step_key TEXT,
            status TEXT NOT NULL,
            claim_lock TEXT,
            claim_expires INTEGER,
            worker_pid INTEGER,
            max_runtime_seconds INTEGER,
            last_heartbeat_at INTEGER,
            started_at INTEGER NOT NULL,
            ended_at INTEGER,
            outcome TEXT,
            summary TEXT,
            metadata TEXT,
            error TEXT
        );
        """
    )
    tasks = [
        ("t_ready", "Ready task", "", "writer", "ready", 5, "user", 1000, None, None, "scratch", None, None, None, None, None, None, 0, None, None, None, None, None, None, None, None, None),
        ("t_blocked", "Needs MT choice", "blocked pending approval", "default", "blocked", 10, "user", 1000, None, None, "scratch", None, None, None, None, None, None, 0, None, None, None, None, None, None, None, None, None),
        ("t_running", "Running task", "", "coder", "running", 1, "user", 1000, 1500, None, "scratch", None, "lock", 1900, "client-a", None, None, 2, 123, None, 100, 2000, 7, None, None, None, None),
        ("t_done", "Done task", "", "reviewer", "done", 1, "user", 1000, 1200, 4500, "scratch", None, None, None, "client-a", "ok", None, 0, None, None, None, None, None, None, None, None, None),
    ]
    conn.executemany(
        """
        INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        tasks,
    )
    conn.executemany(
        """
        INSERT INTO tasks(id, title, body, assignee, status, priority, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "t_review_wrong_profile",
                "Review PR for auth cleanup",
                "Acceptance: review PR and report blocking issues.",
                "coder",
                "ready",
                5,
                "user",
                1000,
            ),
            (
                "t_idea",
                "Idea: agent memory dashboard",
                "Maybe we should someday build a dashboard for agent memory.",
                "default",
                "todo",
                1,
                "user",
                1000,
            ),
            ("t_vague", "Improve docs", "TBD", "default", "todo", 1, "user", 1000),
        ],
    )
    conn.execute("INSERT INTO task_links VALUES (?, ?)", ("t_ready", "t_blocked"))
    conn.execute(
        "INSERT INTO task_comments(task_id, author, body, created_at) VALUES (?, ?, ?, ?)",
        ("t_blocked", "operator", "Needs MT decision on scope", 3000),
    )
    conn.execute(
        "INSERT INTO task_events(task_id, run_id, kind, payload, created_at) VALUES (?, ?, ?, ?, ?)",
        ("t_blocked", None, "blocked", '{"reason":"Need human input"}', 3100),
    )
    conn.execute(
        """
        INSERT INTO task_runs(task_id, profile, status, claim_lock, claim_expires, worker_pid,
                              max_runtime_seconds, last_heartbeat_at, started_at, ended_at,
                              outcome, summary, metadata, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("t_running", "coder", "running", "lock", 1900, 123, 100, 2000, 1500, None, None, None, None, None),
    )
    conn.commit()
    conn.close()


class KanbanCollectorTest(unittest.TestCase):
    def test_collects_all_boards_counts_dependencies_signals_and_since_window(self) -> None:
        collector = load_collector_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "kanban.db"
            state = Path(tmpdir) / "state.json"
            state.write_text(json.dumps({"last_run_at": 4000}), encoding="utf-8")
            create_db(db)

            payload = collector.collect_kanban(db, state, now=10_000, heartbeat_stale_seconds=1000)

        self.assertEqual("kanban_morning_brief", payload["job"])
        self.assertFalse(payload["kanban_mutations"])
        self.assertEqual(2, payload["summary"]["boards"])
        self.assertEqual(7, payload["summary"]["tasks"])
        self.assertEqual(1, payload["summary"]["blocked_tasks"])
        self.assertEqual(1, payload["summary"]["running_or_claimed_tasks"])
        self.assertEqual(1, payload["summary"]["completed_since_last_run"])
        self.assertGreaterEqual(payload["summary"]["tasks_needing_mt"], 1)

        default_board = next(board for board in payload["boards"] if board["board"] == "default")
        blocked = next(task for task in default_board["tasks"] if task["id"] == "t_blocked")
        self.assertEqual(["t_ready"], blocked["dependencies"]["parents"])
        self.assertIn("Needs MT decision", blocked["latest_comments"][0]["body"])

        client_board = next(board for board in payload["boards"] if board["board"] == "client-a")
        stale = client_board["stale_heartbeats_or_claims"][0]
        self.assertEqual("t_running", stale["id"])
        self.assertIn("claim_expired", stale["reasons"])
        self.assertIn("heartbeat_stale", stale["reasons"])
        self.assertIn("multiple_consecutive_failures", stale["reasons"])

    def test_dry_run_cli_prints_json_and_does_not_write_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "kanban.db"
            state = Path(tmpdir) / "state.json"
            create_db(db)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--dry-run", "--db-path", str(db), "--state-path", str(state), "--now", "10000"],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["state_written"])
            self.assertFalse(state.exists())

    def test_cleanup_dry_run_is_recommend_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "kanban.db"
            state = Path(tmpdir) / "state.json"
            create_db(db)
            result = subprocess.run(
                [sys.executable, str(CLEANUP_SCRIPT), "--dry-run", "--db-path", str(db), "--state-path", str(state), "--now", "1000000"],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual("kanban_cleanup_proposal", payload["job"])
            self.assertEqual("approval_ready", payload["proposal_status"])
            self.assertFalse(payload["kanban_mutations"])
            self.assertTrue(payload["no_changes_made"])
            self.assertIn("No Kanban changes were made", payload["safety_notice"])
            self.assertIn("stale_tasks", payload)
            self.assertIn("archivable_items", payload)
            self.assertIn("missing_acceptance_criteria", payload)
            self.assertIn("vague_tasks_needing_rewrite", payload)
            self.assertIn("non_actionable_ideas_for_gbrain", payload)
            self.assertIn("wrong_profile_assignments", payload)
            self.assertGreaterEqual(payload["summary"]["total_recommendations"], 1)
            self.assertTrue(any(item["id"] == "t_review_wrong_profile" for item in payload["wrong_profile_assignments"]))
            self.assertTrue(any(item["id"] == "t_idea" for item in payload["non_actionable_ideas_for_gbrain"]))
            self.assertTrue(any(item["id"] == "t_vague" for item in payload["vague_tasks_needing_rewrite"]))


if __name__ == "__main__":
    unittest.main()
