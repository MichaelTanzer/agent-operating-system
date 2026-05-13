import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "morning-briefing" / "scripts" / "cross_domain_analogy.py"


def load_module():
    spec = importlib.util.spec_from_file_location("cross_domain_analogy", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_script(*args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


class CrossDomainAnalogyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_payload_is_structural_analogy_with_two_or_three_paragraphs(self):
        payload = self.module.build_payload(
            dry_run=True,
            state_pairs=[],
            context={},
            generated_at=datetime(2026, 5, 17, 20, 0, tzinfo=timezone.utc),
        )

        self.assertEqual("cross_domain_analogy", payload["job"])
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["gbrain_writes"])
        self.assertFalse(payload["kanban_mutations"])
        self.assertEqual(2, len(payload["domains"]))
        self.assertIn(payload["domains"][0], self.module.DOMAINS)
        self.assertIn(payload["domains"][1], self.module.DOMAINS)
        self.assertIn("structural analogy", payload["quality_bar"])
        self.assertGreaterEqual(len(payload["paragraphs"]), 2)
        self.assertLessEqual(len(payload["paragraphs"]), 3)
        for paragraph in payload["paragraphs"]:
            self.assertGreater(len(paragraph.split()), 30)
        self.assertEqual([], self.module.validate_payload(payload))

    def test_dry_run_json_cli_does_not_write_local_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script("--dry-run", "--json", "--state-dir", tmpdir)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertFalse((Path(tmpdir) / "analogy_history.jsonl").exists())

    def test_plain_output_is_letter_ready_and_not_generic_prompt_scaffold(self):
        result = run_script("--dry-run")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn("Cross-Domain Analogy", result.stdout)
        self.assertIn("Dear MT,", result.stdout)
        self.assertNotIn("TODO", result.stdout)
        self.assertNotIn("lorem", result.stdout.lower())
        paragraphs = [p for p in result.stdout.split("\n\n") if p.strip()]
        body_paragraphs = [p for p in paragraphs if not p.startswith("[DRY RUN]") and not p.startswith("Cross-Domain")]
        self.assertGreaterEqual(len(body_paragraphs), 2)
        self.assertLessEqual(len(body_paragraphs), 3)

    def test_local_history_rotates_away_from_recent_domain_pair(self):
        first_pair = (self.module.DOMAINS[0], self.module.DOMAINS[1])
        second_pair = self.module.select_domain_pair(state_pairs=[first_pair], context={})

        self.assertNotEqual(first_pair, second_pair)
        self.assertEqual((self.module.DOMAINS[1], self.module.DOMAINS[2]), second_pair)

    def test_context_read_takes_precedence_over_local_rotation(self):
        context = {
            "preferred_pair": ["ceramics", "TanzerBot"],
            "source_notes": ["A rough thesis should be centered before it is fired."],
            "recent_analogies": [
                {"domains": ["investment research craft", "AI agent architectures"]}
            ],
        }
        payload = self.module.build_payload(dry_run=True, state_pairs=[], context=context)

        self.assertEqual(["ceramics", "TanzerBot"], payload["domains"])
        self.assertEqual("context", payload["source"])
        self.assertIn("A rough thesis", " ".join(payload["context_notes"]))
        self.assertFalse(payload["gbrain_writes"])

    def test_live_run_appends_local_history_without_gbrain_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script("--json", "--state-dir", tmpdir)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            history = Path(tmpdir) / "analogy_history.jsonl"
            self.assertTrue(history.exists())
            record = json.loads(history.read_text(encoding="utf-8").strip())
            self.assertEqual(payload["domains"], record["domains"])
            self.assertFalse(payload["gbrain_writes"])


if __name__ == "__main__":
    unittest.main()
