#!/usr/bin/env python3
"""Run and verify Phase 1 Morning Briefing dry-runs.

The runner is intentionally side-effect free: it only invokes dry-run commands,
captures their output, and validates the Phase 1 output contracts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in stripped envs
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


PHASE1_JOBS = ("dc_weather", "gratitude", "no_do", "overnight_ideas")
JSON_VERIFICATION_JOBS = {"gratitude", "no_do", "overnight_ideas"}
PYTHON_BIN = "python3"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JOBS_YAML = REPO_ROOT / "morning-briefing" / "config" / "jobs.yaml"


@dataclass(frozen=True)
class JobResult:
    job: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    errors: list[str]

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "job": self.job,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "ok": self.ok,
            "errors": self.errors,
        }


def load_jobs(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    jobs = config.get("jobs")
    if not isinstance(jobs, dict):
        raise ValueError(f"{path} does not contain a jobs mapping")
    return jobs


def normalize_python_command(command: list[str]) -> list[str]:
    if not command:
        return command

    executable = Path(command[0]).name
    if executable == "python" or executable.startswith("python3"):
        return [PYTHON_BIN, *command[1:]]
    return command


def dry_run_command(job_name: str, spec: dict[str, Any]) -> list[str]:
    raw_command = spec.get("dry_run_cmd")
    if raw_command:
        command = shlex.split(str(raw_command))
    else:
        script = spec.get("script")
        if not script:
            raise ValueError(f"{job_name} has neither dry_run_cmd nor script")
        command = [PYTHON_BIN, str(script), "--dry-run"]

    command = normalize_python_command(command)
    if "--dry-run" not in command:
        command.append("--dry-run")
    if job_name in JSON_VERIFICATION_JOBS and "--json" not in command:
        command.append("--json")
    return command


def run_command(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "MORNING_REPO_ROOT": str(REPO_ROOT),
            "MORNING_PHASE1_DRY_RUN": "1",
        }
    )
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


def nonempty_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def parse_json_output(job_name: str, stdout: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return None, [f"{job_name}: stdout is not valid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{job_name}: JSON output is not an object"]
    return payload, []


def validate_weather(stdout: str, spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    lines = nonempty_lines(stdout)
    max_lines = int((spec.get("output_contract") or {}).get("max_lines", 7))

    if not lines:
        errors.append("dc_weather: stdout is empty")
    if len(lines) > max_lines:
        errors.append(f"dc_weather: expected <= {max_lines} non-empty lines, got {len(lines)}")
    if not lines or "DC Weather" not in lines[0]:
        errors.append("dc_weather: first line does not identify the weather brief")
    if "sample" not in stdout:
        errors.append("dc_weather: dry-run output did not report deterministic sample data")
    return errors


def validate_gratitude(stdout: str) -> list[str]:
    payload, errors = parse_json_output("gratitude", stdout)
    if errors:
        return errors

    text = ((payload or {}).get("message") or {}).get("text", "")
    delivery = (payload or {}).get("delivery") or {}
    if delivery.get("expects_response") is not True:
        errors.append("gratitude: expects_response is not true")
    if "what are three things you're grateful for today?" not in text:
        errors.append("gratitude: prompt text is missing the gratitude question")
    if "1.\n2.\n3." not in text:
        errors.append("gratitude: prompt text is missing the three response slots")
    return errors


def validate_no_do(stdout: str) -> list[str]:
    payload, errors = parse_json_output("no_do", stdout)
    if errors:
        return errors

    recommendation = str((payload or {}).get("recommendation", ""))
    if (payload or {}).get("recommend_only") is not True:
        errors.append("no_do: recommend_only is not true")
    if (payload or {}).get("kanban_mutations") is not False:
        errors.append("no_do: kanban_mutations is not false")
    if (payload or {}).get("gbrain_writes") is not False:
        errors.append("no_do: gbrain_writes is not false")
    if sentence_count(recommendation) > 2:
        errors.append("no_do: recommendation exceeds 2 sentences")
    if not recommendation:
        errors.append("no_do: recommendation is empty")
    return errors


def validate_overnight_ideas(stdout: str) -> list[str]:
    payload, errors = parse_json_output("overnight_ideas", stdout)
    if errors:
        return errors

    buckets = (payload or {}).get("buckets", [])
    if not isinstance(buckets, list):
        return ["overnight_ideas: buckets is not a list"]

    total_ideas = 0
    if len(buckets) != 4:
        errors.append(f"overnight_ideas: expected 4 buckets, got {len(buckets)}")
    for bucket in buckets:
        if not isinstance(bucket, dict):
            errors.append("overnight_ideas: bucket is not an object")
            continue
        ideas = bucket.get("ideas", [])
        if not isinstance(ideas, list):
            errors.append(f"overnight_ideas: {bucket.get('id', '<unknown>')} ideas is not a list")
            continue
        total_ideas += len(ideas)
        if len(ideas) != 3:
            errors.append(f"overnight_ideas: {bucket.get('id', '<unknown>')} expected 3 ideas")

    if total_ideas != 12:
        errors.append(f"overnight_ideas: expected 12 total ideas, got {total_ideas}")
    if (payload or {}).get("auto_task_creation") is not False:
        errors.append("overnight_ideas: auto_task_creation is not false")
    if (payload or {}).get("gbrain_writes") is not False:
        errors.append("overnight_ideas: gbrain_writes is not false")
    return errors


def validate_job(job_name: str, stdout: str, spec: dict[str, Any]) -> list[str]:
    validators = {
        "dc_weather": lambda output: validate_weather(output, spec),
        "gratitude": validate_gratitude,
        "no_do": validate_no_do,
        "overnight_ideas": validate_overnight_ideas,
    }
    return validators[job_name](stdout)


def run_job(job_name: str, spec: dict[str, Any], timeout_seconds: int) -> JobResult:
    command = dry_run_command(job_name, spec)
    try:
        completed = run_command(command, timeout_seconds)
        errors = []
        if completed.returncode != 0:
            errors.append(f"{job_name}: command exited {completed.returncode}")
        errors.extend(validate_job(job_name, completed.stdout, spec))
        return JobResult(
            job=job_name,
            command=command,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            errors=errors,
        )
    except subprocess.TimeoutExpired as exc:
        return JobResult(
            job=job_name,
            command=command,
            exit_code=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            errors=[f"{job_name}: command timed out after {timeout_seconds}s"],
        )


def run_phase1(jobs_yaml: Path, timeout_seconds: int) -> list[JobResult]:
    jobs = load_jobs(jobs_yaml)
    results: list[JobResult] = []
    for job_name in PHASE1_JOBS:
        spec = jobs.get(job_name)
        if not isinstance(spec, dict):
            results.append(
                JobResult(
                    job=job_name,
                    command=[],
                    exit_code=1,
                    stdout="",
                    stderr="",
                    errors=[f"{job_name}: job is missing from {jobs_yaml}"],
                )
            )
            continue
        results.append(run_job(job_name, spec, timeout_seconds))
    return results


def print_text_report(results: list[JobResult]) -> None:
    for index, result in enumerate(results):
        if index:
            print()
        status = "PASS" if result.ok else "FAIL"
        print(f"=== {result.job} [{status}] ===")
        print(f"command: {shlex.join(result.command)}")
        print(f"exit_code: {result.exit_code}")
        if result.errors:
            print("errors:")
            for error in result.errors:
                print(f"- {error}")
        print("stdout:")
        print(result.stdout.rstrip() or "<empty>")
        if result.stderr:
            print("stderr:")
            print(result.stderr.rstrip())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 1 Morning Briefing dry-runs")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable verification output")
    parser.add_argument(
        "--jobs-yaml",
        type=Path,
        default=DEFAULT_JOBS_YAML,
        help="Path to jobs.yaml",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Per-job timeout in seconds",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.timeout <= 0:
        print("ERROR: --timeout must be positive", file=sys.stderr)
        return 2

    try:
        results = run_phase1(args.jobs_yaml, args.timeout)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    ok = all(result.ok for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "jobs": [result.as_dict() for result in results]}, indent=2))
    else:
        print_text_report(results)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
