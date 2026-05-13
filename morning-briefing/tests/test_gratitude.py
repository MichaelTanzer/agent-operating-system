from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "gratitude.py"
JOBS_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "jobs.yaml"


def load_gratitude_module():
    spec = importlib.util.spec_from_file_location("gratitude", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GratitudeScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gratitude = load_gratitude_module()

    def run_main(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.gratitude.main(list(args))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_json_output_is_deterministic_and_verifiable(self) -> None:
        first_code, first_stdout, first_stderr = self.run_main("--json")
        second_code, second_stdout, second_stderr = self.run_main("--json")

        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first_stdout, second_stdout)
        self.assertEqual(first_stderr, second_stderr)

        payload = json.loads(first_stdout)
        self.assertEqual(payload["job"], "gratitude")
        self.assertFalse(payload["dry_run"])
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["delivery"]["mode"], "separate_interactive_message")
        self.assertTrue(payload["delivery"]["expects_response"])
        self.assertEqual(payload["message"]["expected_response_points"], 3)
        self.assertIn("MT, what are three things", payload["message"]["text"])
        self.assertIn("config", payload)

    def test_dry_run_prints_separate_interactive_message(self) -> None:
        exit_code, stdout, _stderr = self.run_main("--dry-run")

        self.assertEqual(exit_code, 0)
        self.assertIn("[DRY RUN] gratitude.py", stdout)
        self.assertIn("separate interactive message", stdout)
        self.assertIn("Please reply with three short points:", stdout)
        self.assertIn("1.\n2.\n3.", stdout)

    def test_live_output_is_only_the_prompt_message(self) -> None:
        exit_code, stdout, stderr = self.run_main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, self.gratitude.PROMPT_TEXT + "\n")

    def test_live_prompt_matches_jobs_yaml_contract(self) -> None:
        jobs_config = yaml.safe_load(JOBS_YAML_PATH.read_text(encoding="utf-8"))
        contract_text = jobs_config["jobs"]["gratitude"]["output_contract"]["text"]

        self.assertEqual(contract_text, self.gratitude.PROMPT_TEXT)


if __name__ == "__main__":
    unittest.main()
