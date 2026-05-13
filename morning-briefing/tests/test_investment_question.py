from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "morning-briefing" / "scripts" / "investment_question.py"


def load_module():
    spec = importlib.util.spec_from_file_location("investment_question", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_script(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


class InvestmentQuestionTest(unittest.TestCase):
    def test_plain_dry_run_emits_single_researchable_question(self):
        result = run_script("--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.startswith("[DRY RUN] For "))
        self.assertTrue(result.stdout.strip().endswith("?"))
        self.assertLessEqual(sentence_count(result.stdout), 2)
        self.assertIn("evidence", result.stdout)
        self.assertIn("filings", result.stdout)
        self.assertNotIn("market regime", result.stdout.lower())

    def test_json_output_marks_read_only_and_watchlist_anchored(self):
        result = run_script("--dry-run", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["job"], "investment_question")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["gbrain_writes"])
        self.assertFalse(payload["kanban_mutations"])
        self.assertIn(payload["source"], {"watchlist_deterministic_seed", "gbrain_active_thread"})
        self.assertIn(payload["company"]["name"], payload["question"])
        self.assertTrue(payload["question"].endswith("?"))
        self.assertLessEqual(sentence_count(payload["question"]), 2)

    def test_gbrain_fixture_can_select_active_watchlist_thread(self):
        fixture = {
            "threads": [
                {
                    "title": "TanzerBot active thread: RXO Coyote integration",
                    "summary": "Watch RXO gross margin per load and Coyote integration as the live brokerage-cycle question.",
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
            json.dump(fixture, handle)
            handle.flush()
            result = run_script("--json", "--gbrain-json", handle.name)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["source"], "gbrain_active_thread")
        self.assertEqual(payload["company"]["name"], "RXO")
        self.assertEqual(payload["material_topic"], "Coyote integration")
        self.assertIn("RXO", payload["question"])
        self.assertFalse(payload["gbrain_writes"])

    def test_fallback_is_deterministic_for_same_date(self):
        module = load_module()
        generated_at = datetime(2026, 5, 13, 10, 20, tzinfo=timezone.utc)

        first = module.build_payload(dry_run=True, generated_at=generated_at, gbrain_fixture=Path("/definitely/missing.json"))
        second = module.build_payload(dry_run=True, generated_at=generated_at, gbrain_fixture=Path("/definitely/missing.json"))

        self.assertEqual(first["source"], "watchlist_deterministic_seed")
        self.assertEqual(first["company"], second["company"])
        self.assertEqual(first["material_topic"], second["material_topic"])
        self.assertEqual(first["question"], second["question"])

    def test_question_validator_rejects_macro_market_regime_language(self):
        module = load_module()
        company = module.Company(
            name="Aon",
            ticker="AON",
            sector="insurance_broking",
            sector_label="Insurance Brokerage & Risk Advisory",
            material_topics=("organic_growth",),
            query_focus=(),
            aliases=(),
        )

        errors = module.validate_question("For Aon, is the market regime favorable?", company)

        self.assertIn("question contains generic macro/market-regime language", errors)


if __name__ == "__main__":
    unittest.main()
