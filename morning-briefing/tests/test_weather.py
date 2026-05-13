import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEATHER_PATH = REPO_ROOT / "morning-briefing" / "scripts" / "weather.py"


def load_weather():
    spec = importlib.util.spec_from_file_location("weather", WEATHER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WeatherBriefTest(unittest.TestCase):
    def test_dry_run_plain_text_contract(self):
        weather = load_weather()
        brief = weather.get_brief(dry_run=True)
        text = weather.format_plain(brief, dry_run=True)

        lines = text.splitlines()
        self.assertEqual(7, len(lines))
        self.assertIn("[DRY RUN] DC Weather - sample", lines[0])
        self.assertIn("High 78F / Low 61F", text)
        self.assertIn("Umbrella: no.", text)
        self.assertIn("AQI: unavailable | Pollen: unavailable", text)

    def test_dry_run_json_cli(self):
        result = subprocess.run(
            [sys.executable, str(WEATHER_PATH), "--dry-run", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual("Washington, DC", payload["location"])
        self.assertEqual("sample", payload["status"])
        self.assertEqual(78, payload["high_f"])
        self.assertEqual("unavailable", payload["aqi"])

    def test_network_failure_degrades_without_exception(self):
        weather = load_weather()

        def fail(_timeout_seconds):
            raise weather.WeatherFetchError

        original_live_payload = weather.live_payload
        try:
            weather.live_payload = fail
            brief = weather.get_brief(dry_run=False)
        finally:
            weather.live_payload = original_live_payload

        self.assertEqual("degraded", brief["status"])
        self.assertEqual("unavailable", brief["current_conditions"])
        self.assertEqual("check before leaving", brief["umbrella"])
        self.assertEqual("unavailable", brief["pollen"])


if __name__ == "__main__":
    unittest.main()
