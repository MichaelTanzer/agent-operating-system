import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "morning-briefing" / "scripts" / "overnight_ideas.py"


def load_module():
    spec = importlib.util.spec_from_file_location("overnight_ideas", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OvernightIdeasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_payload_matches_output_contract(self):
        payload = self.module.build_payload(
            dry_run=True,
            seen_ids=set(),
            generated_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        )

        self.assertEqual("overnight_ideas", payload["job"])
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["auto_task_creation"])
        self.assertFalse(payload["gbrain_writes"])
        self.assertEqual(
            [
                "Kanban good -> great",
                "Extend MT's capabilities",
                "Coding stack efficacy",
                "New project ideas",
            ],
            [bucket["label"] for bucket in payload["buckets"]],
        )

        for bucket in payload["buckets"]:
            self.assertEqual(3, len(bucket["ideas"]))
            for idea in bucket["ideas"]:
                self.assertEqual(2, self.module.sentence_count(idea), idea)

        self.assertEqual([], self.module.validate_payload(payload))

    def test_dry_run_json_cli_does_not_write_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["MORNING_STATE_DIR"] = tmpdir
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--dry-run", "--json"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(4, len(payload["buckets"]))
            self.assertFalse((Path(tmpdir) / "idea_history.jsonl").exists())

    def test_bad_history_degrades_gracefully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "idea_history.jsonl"
            path.write_text("not-json\n{}\n", encoding="utf-8")

            self.assertEqual(set(), self.module.load_history(path))

    def test_history_rotates_seen_ideas(self):
        first_bucket = self.module.BUCKETS[0]
        seen = {
            self.module.idea_id(first_bucket.bucket_id, idea)
            for idea in first_bucket.ideas[:3]
        }

        selected = self.module.select_ideas(first_bucket, seen)

        self.assertEqual(list(first_bucket.ideas[3:6]), selected)


if __name__ == "__main__":
    unittest.main()
