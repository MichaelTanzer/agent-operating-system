#!/usr/bin/env python3
"""
config_loader.py — Morning Briefing System config loader

Resolves config from two sources:
  1. Source-controlled: <repo>/morning-briefing/config/jobs.yaml
  2. Runtime overrides: ~/.hermes/morning/config.yaml (not in git)

Usage:
    from config_loader import load_config, get_job
    config = load_config()
    job = get_job(config, "dc_weather")

    # Or as a CLI dry-run check:
    python morning-briefing/scripts/config_loader.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    """Return the agent-operating-system repo root.

    Checks (in order):
      1. MORNING_REPO_ROOT env var
      2. HERMES_KANBAN_WORKSPACE env var (worktree tasks)
      3. Walk up from this script's location looking for morning-briefing/
      4. ~/dev/repos/agent-operating-system
    """
    if root := os.environ.get("MORNING_REPO_ROOT"):
        return Path(root).expanduser().resolve()

    if ws := os.environ.get("HERMES_KANBAN_WORKSPACE"):
        p = Path(ws).expanduser().resolve()
        if (p / "morning-briefing").exists():
            return p

    # Walk up from this file
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "morning-briefing").exists():
            return ancestor

    # Fallback
    return Path("~/dev/repos/agent-operating-system").expanduser().resolve()


def _jobs_yaml_path() -> Path:
    return _repo_root() / "morning-briefing" / "config" / "jobs.yaml"


def _runtime_config_path() -> Path:
    hermes_home = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    return hermes_home / "morning" / "config.yaml"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def _deep_merge(base: dict, override: dict) -> dict:
    """Shallow-merge override on top of base (one level deep for now)."""
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return merged


def load_config(jobs_yaml: Path | None = None, runtime_yaml: Path | None = None) -> dict:
    """Load and merge the two config layers.

    Returns a dict with keys:
      system   — system-level settings
      jobs     — per-job specs
      _paths   — resolved file paths (for debugging)
    """
    jobs_path = jobs_yaml or _jobs_yaml_path()
    runtime_path = runtime_yaml or _runtime_config_path()

    if not jobs_path.exists():
        raise FileNotFoundError(
            f"jobs.yaml not found at {jobs_path}. "
            f"Set MORNING_REPO_ROOT or run from within the repo."
        )

    base = _load_yaml(jobs_path)
    runtime = _load_yaml(runtime_path)

    # Apply runtime overrides to system block
    system = dict(base.get("system", {}))
    if "delivery" in runtime:
        rt_delivery = runtime["delivery"]
        base_delivery = system.get("delivery", {})
        if isinstance(rt_delivery, dict) and isinstance(base_delivery, dict):
            system["delivery"] = {**base_delivery, **rt_delivery}
        elif isinstance(rt_delivery, dict) and "platform" in rt_delivery:
            # runtime is a dict, base is a string — extract platform
            system["delivery"] = rt_delivery["platform"]
        elif isinstance(rt_delivery, str):
            system["delivery"] = rt_delivery
        else:
            system["delivery"] = rt_delivery
    if "watchlist_path" in runtime:
        system["watchlist_path"] = runtime["watchlist_path"]
    if "gbrain_db_url" in runtime:
        system["gbrain_db_url"] = runtime["gbrain_db_url"]

    # Expand env vars in gbrain_db_url
    if "gbrain_db_url" in system:
        system["gbrain_db_url"] = os.path.expandvars(system["gbrain_db_url"])

    # Also check env var directly
    if not system.get("gbrain_db_url"):
        system["gbrain_db_url"] = os.environ.get("GBRAIN_DATABASE_URL", "")

    # Expand ~ in state_dir
    if "state_dir" in system:
        system["state_dir"] = str(Path(system["state_dir"]).expanduser())

    return {
        "system": system,
        "jobs": base.get("jobs", {}),
        "_paths": {
            "jobs_yaml": str(jobs_path),
            "runtime_yaml": str(runtime_path),
            "runtime_yaml_exists": runtime_path.exists(),
        },
    }


def get_job(config: dict, job_name: str) -> dict:
    """Return a single job spec, merged with system defaults."""
    jobs = config.get("jobs", {})
    if job_name not in jobs:
        raise KeyError(f"Job '{job_name}' not found in config. Available: {list(jobs)}")
    return jobs[job_name]


def get_enabled_jobs(config: dict) -> dict[str, Any]:
    """Return only the enabled jobs."""
    return {
        name: spec
        for name, spec in config["jobs"].items()
        if spec.get("enabled", True)
    }


def state_dir(config: dict) -> Path:
    return Path(config["system"]["state_dir"])


def last_run_path(config: dict, job_name: str) -> Path:
    return state_dir(config) / "last_run" / f"{job_name}.json"


# ---------------------------------------------------------------------------
# CLI / dry-run
# ---------------------------------------------------------------------------

def _print_summary(config: dict) -> None:
    paths = config["_paths"]
    system = config["system"]
    jobs = config["jobs"]

    print(f"Morning Briefing System — Config Loader")
    print(f"  jobs.yaml:      {paths['jobs_yaml']}")
    print(f"  runtime.yaml:   {paths['runtime_yaml']} ({'found' if paths['runtime_yaml_exists'] else 'not found — using defaults'})")
    print(f"  timezone:       {system.get('timezone', 'not set')}")
    print(f"  delivery:       {system.get('delivery', 'not set')}")
    print(f"  state_dir:      {system.get('state_dir', 'not set')}")
    print(f"  watchlist_path: {system.get('watchlist_path', 'not set')}")
    print(f"  gbrain_db_url:  {'set' if system.get('gbrain_db_url') else 'not set'}")
    print()
    print(f"Jobs ({len(jobs)} total):")

    for name, spec in jobs.items():
        status = "enabled " if spec.get("enabled", True) else "disabled"
        impl = spec.get("implementation", "?")
        cron = spec.get("cron", "?")
        print(f"  [{status}] {name:30s}  impl={impl:6s}  cron={cron}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Morning Briefing config loader")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved config and exit")
    parser.add_argument("--job", help="Print spec for a specific job")
    parser.add_argument("--jobs-yaml", help="Override path to jobs.yaml")
    parser.add_argument("--runtime-yaml", help="Override path to runtime config.yaml")
    args = parser.parse_args()

    jobs_yaml = Path(args.jobs_yaml) if args.jobs_yaml else None
    runtime_yaml = Path(args.runtime_yaml) if args.runtime_yaml else None

    try:
        config = load_config(jobs_yaml, runtime_yaml)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.job:
        try:
            spec = get_job(config, args.job)
            import json
            print(json.dumps(spec, indent=2))
        except KeyError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        _print_summary(config)

    if args.dry_run:
        print()
        print("Dry-run: config loaded successfully.")


if __name__ == "__main__":
    main()
