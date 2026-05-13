import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "morning-briefing" / "scripts" / "gbrain_recall.py"


def load_module():
    spec = importlib.util.spec_from_file_location("gbrain_recall", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_script(*args, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
    )


class GbrainRecallTest(unittest.TestCase):
    def test_plain_dry_run_falls_back_to_three_to_five_lines_without_writes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--dry-run",
                "--state-dir",
                tmpdir,
                env={"PATH": tmpdir, "HOME": tmpdir},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            lines = [line for line in result.stdout.splitlines() if line.strip()]
            self.assertGreaterEqual(len(lines), 3)
            self.assertLessEqual(len(lines), 5)
            self.assertTrue(lines[0].startswith("[DRY RUN] Gbrain Recall"))
            self.assertIn("Origin date:", result.stdout)
            self.assertIn("fallback", result.stdout.lower())
            self.assertFalse((Path(tmpdir) / "last_run" / "gbrain_recall.json").exists())

    def test_json_dry_run_contract_marks_read_only_and_origin_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--dry-run",
                "--json",
                "--state-dir",
                tmpdir,
                env={"PATH": tmpdir, "HOME": tmpdir},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["job"], "gbrain_recall")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["gbrain_writes"])
        self.assertFalse(payload["history_writes"])
        self.assertEqual(payload["source_status"], "fallback")
        self.assertIn("origin_date", payload["note"])
        self.assertTrue(payload["note"]["origin_date"])

    def test_live_run_records_history_only_in_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--json",
                "--state-dir",
                tmpdir,
                env={"PATH": tmpdir, "HOME": tmpdir},
            )
            history_path = Path(tmpdir) / "last_run" / "gbrain_recall.json"

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["history_writes"])
            self.assertFalse(payload["gbrain_writes"])
            self.assertTrue(history_path.exists())
            history = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["note"]["id"], history["last_note_id"])
            self.assertIn(payload["note"]["id"], history["recalled"])

    def test_recency_exclusion_selects_unrecalled_candidate(self):
        module = load_module()
        today = date(2026, 5, 13)
        recent = module.Candidate(
            note_id="recent-note",
            slug="recent",
            title="Recent note",
            origin_date="2026-05-01",
            summary="Recently recalled.",
            source="fixture",
            score=99,
        )
        older = module.Candidate(
            note_id="older-note",
            slug="older",
            title="Older note",
            origin_date="2026-04-01",
            summary="Eligible recall.",
            source="fixture",
            score=1,
        )
        history = {"recalled": {"recent-note": (today - timedelta(days=3)).isoformat()}}

        payload = module.build_payload(
            dry_run=True,
            history=history,
            today=today,
            candidates=[recent, older],
        )

        self.assertEqual(payload["note"]["id"], "older-note")
        self.assertFalse(payload["note"]["recalled_within_exclusion_window"])
        self.assertFalse(payload["gbrain_writes"])

    def test_parses_gbrain_tabular_listing_and_filters_cli_warning(self):
        module = load_module()
        output = "\n".join(
            [
                '[ai.gateway] recipe "google" declares an embedding touchpoint',
                "projects/agent-operating-system/current_state\tproject\t2026-05-11\tCurrent State — agent-operating-system",
                "No results.",
            ]
        )

        candidates = module.parse_gbrain_listing(output, score=10)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].slug, "projects/agent-operating-system/current_state")
        self.assertEqual(candidates[0].origin_date, "2026-05-11")
        self.assertIn("Current State", candidates[0].title)


if __name__ == "__main__":
    unittest.main()
