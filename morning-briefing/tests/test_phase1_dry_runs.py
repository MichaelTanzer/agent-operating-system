from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "morning-briefing" / "scripts" / "run_phase1_dry_runs.py"


class Phase1DryRunsTest(unittest.TestCase):
    def test_runner_executes_phase1_jobs_and_validates_contracts(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])

        jobs = {job["job"]: job for job in payload["jobs"]}
        self.assertEqual(
            {"dc_weather", "gratitude", "no_do", "overnight_ideas"},
            set(jobs),
        )

        for job in jobs.values():
            self.assertTrue(job["ok"], job)
            self.assertEqual(0, job["exit_code"])
            self.assertEqual("python3", job["command"][0])
            self.assertIn("--dry-run", job["command"])
            self.assertNotEqual("python", job["command"][0])

        weather_lines = [line for line in jobs["dc_weather"]["stdout"].splitlines() if line.strip()]
        self.assertLessEqual(len(weather_lines), 7)
        self.assertIn("sample", jobs["dc_weather"]["stdout"])

        gratitude = json.loads(jobs["gratitude"]["stdout"])
        self.assertTrue(gratitude["delivery"]["expects_response"])
        self.assertIn("what are three things", gratitude["message"]["text"])

        no_do = json.loads(jobs["no_do"]["stdout"])
        self.assertTrue(no_do["recommend_only"])
        self.assertFalse(no_do["kanban_mutations"])
        self.assertFalse(no_do["gbrain_writes"])

        overnight = json.loads(jobs["overnight_ideas"]["stdout"])
        self.assertEqual(4, len(overnight["buckets"]))
        self.assertEqual(12, sum(len(bucket["ideas"]) for bucket in overnight["buckets"]))
        self.assertFalse(overnight["auto_task_creation"])
        self.assertFalse(overnight["gbrain_writes"])


if __name__ == "__main__":
    unittest.main()
