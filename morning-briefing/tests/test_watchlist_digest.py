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
SCRIPT_PATH = REPO_ROOT / "morning-briefing" / "scripts" / "watchlist_digest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("watchlist_digest", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WatchlistDigestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_manual_full_run_checks_exact_23_companies_and_surfaces_material_only(self):
        payload = self.module.build_payload(
            dry_run=True,
            generated_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        )

        self.assertEqual("company_watchlist", payload["job"])
        self.assertEqual(23, payload["approved_company_count"])
        self.assertEqual(23, payload["checked_company_count"])
        self.assertEqual(23, len(payload["checked_companies"]))
        self.assertGreater(payload["material_item_count"], 0)
        self.assertLessEqual(payload["material_item_count"], payload["max_items"])
        self.assertTrue(payload["consulting_industry_signal_included"])
        self.assertIn("Checked 23/23 approved companies", payload["coverage_note"])
        self.assertEqual([], self.module.validate_payload(payload))

        for item in payload["items"]:
            self.assertGreaterEqual(item["score"], 6)
            self.assertTrue(item["url"])
            self.assertTrue(item["why_it_matters"])
            self.assertNotIn("tier5_low_quality_or_noise", item["source_tier"])

    def test_company_filter_checks_only_requested_company(self):
        payload = self.module.build_payload(dry_run=True, company="AON")

        self.assertEqual(23, payload["approved_company_count"])
        self.assertEqual(1, payload["checked_company_count"])
        self.assertEqual("AON", payload["checked_companies"][0]["ticker"])
        self.assertIn("Checked 1/23 approved companies", payload["coverage_note"])
        self.assertEqual([], self.module.validate_payload(payload))

    def test_dedupe_filtering_removes_duplicate_and_low_quality_noise(self):
        duplicate = self.module.PROTOTYPE_CANDIDATES[0]
        candidates = list(self.module.PROTOTYPE_CANDIDATES) + [duplicate]
        unique = self.module.dedupe(candidates)
        self.assertEqual(len(self.module.PROTOTYPE_CANDIDATES), len(unique))

        watchlist, rubric = self.module.load_taxonomy(self.module.resolve_watchlist_path())
        checked = self.module.checked_companies(watchlist)
        noisy = [candidate for candidate in unique if candidate.source_tier == "tier5_low_quality_or_noise"]
        self.assertTrue(noisy)
        for candidate in noisy:
            companies = self.module.matched_companies(candidate, checked)
            scored = self.module.score_candidate(candidate, rubric, companies)
            self.assertEqual("excluded", scored.status)

    def test_json_cli_emits_links_why_it_matters_and_coverage_note(self):
        env = os.environ.copy()
        env["MORNING_REPO_ROOT"] = str(REPO_ROOT)
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--dry-run", "--json"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(23, payload["checked_company_count"])
        self.assertIn("coverage_note", payload)
        self.assertTrue(payload["items"])
        for item in payload["items"]:
            self.assertIn("http", item["url"])
            self.assertIn("Why", f"Why it matters: {item['why_it_matters']}")

    def test_external_candidate_file_can_be_scored(self):
        rows = [
            {
                "title": "Marsh McLennan reports organic growth and margin expansion in earnings release",
                "source": "Marsh McLennan Investor Relations",
                "source_tier": "tier1_primary",
                "url": "https://www.marshmclennan.com/investors.html",
                "published_at": "2026-05-13",
                "summary": "Primary earnings release names organic growth, fiduciary income, and margin expansion.",
                "matched_tickers": ["MMC"],
                "matched_companies": ["Marsh McLennan"],
                "materiality_signals": ["organic_growth_or_share_gain", "margin_structure"],
                "primary_data": True,
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "candidates.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            payload = self.module.build_payload(dry_run=True, input_candidates=path)

        self.assertEqual(1, payload["material_item_count"])
        self.assertEqual("MMC", payload["items"][0]["ticker"])


if __name__ == "__main__":
    unittest.main()
