import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "morning-briefing" / "scripts" / "no_do.py"


def load_no_do_module():
    spec = importlib.util.spec_from_file_location("no_do", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_no_do(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def sentence_count(text):
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


class NoDoTest(unittest.TestCase):
    def test_plain_text_output_is_labeled_and_concise(self):
        result = run_no_do()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("One Thing to Not Do Today:", result.stdout)
        self.assertIn("smallest accepted slice", result.stdout)
        self.assertLessEqual(sentence_count(result.stdout), 2)

    def test_dry_run_output_is_labeled_and_concise(self):
        result = run_no_do("--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.startswith("[DRY RUN] One Thing to Not Do Today:"))
        self.assertLessEqual(sentence_count(result.stdout), 2)

    def test_json_output_marks_recommend_only_no_writes_or_mutations(self):
        result = run_no_do("--json", "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["label"], "One Thing to Not Do Today")
        self.assertTrue(payload["dry_run"])
        self.assertTrue(payload["recommend_only"])
        self.assertFalse(payload["kanban_mutations"])
        self.assertFalse(payload["gbrain_writes"])
        self.assertEqual(payload["source"], "deterministic_phase1_fallback")

    def test_fallback_is_deterministic_and_targets_known_failure_modes(self):
        no_do = load_no_do_module()

        first = no_do.build_payload()
        second = no_do.build_payload()

        self.assertEqual(first, second)
        recommendation = first["recommendation"]
        self.assertIn("architecture", recommendation)
        self.assertIn("scope", recommendation)
        self.assertIn("abstraction", recommendation)


if __name__ == "__main__":
    unittest.main()
