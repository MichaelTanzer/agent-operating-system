#!/usr/bin/env python3
"""
investment_question.py - Weekday One Investment Question MVP.

Emits a single company/sector-anchored research question for MT's Morning
Briefing System. The job is read-only: it may consult Gbrain for active
TanzerBot/watchlist threads, but never writes to Gbrain or Kanban. If Gbrain is
unavailable or empty, it falls back to the source-controlled 23-company
watchlist and a deterministic date seed.

Dry-run:
    python3 morning-briefing/scripts/investment_question.py --dry-run
    python3 morning-briefing/scripts/investment_question.py --dry-run --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in stripped envs
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

JOB_NAME = "investment_question"
FALLBACK_SOURCE = "watchlist_deterministic_seed"
GBRAIN_SOURCE = "gbrain_active_thread"
DEFAULT_GBRAIN_QUERIES = (
    "TanzerBot active research threads watchlist",
    "watchlist active investment research thread",
    "morning briefing investment question watchlist",
)
GENERIC_MARKET_TERMS = (
    "market regime",
    "fed",
    "interest rates",
    "inflation",
    "recession",
    "soft landing",
    "risk assets",
    "multiple expansion",
)


@dataclass(frozen=True)
class Company:
    name: str
    ticker: str
    sector: str
    sector_label: str
    material_topics: tuple[str, ...]
    query_focus: tuple[str, ...]
    aliases: tuple[str, ...]


def repo_root() -> Path:
    if root := os.environ.get("MORNING_REPO_ROOT"):
        return Path(root).expanduser().resolve()
    if ws := os.environ.get("HERMES_KANBAN_WORKSPACE"):
        workspace = Path(ws).expanduser().resolve()
        if (workspace / "morning-briefing").exists():
            return workspace
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "morning-briefing").exists():
            return ancestor
    return Path("~/dev/repos/agent-operating-system").expanduser().resolve()


def default_watchlist_path() -> Path:
    return repo_root() / "morning-briefing" / "config" / "watchlist.yaml"


def load_watchlist(path: Path | None = None) -> list[Company]:
    watchlist_path = (path or default_watchlist_path()).expanduser()
    with watchlist_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    companies: list[Company] = []
    for item in raw.get("companies", []):
        if not isinstance(item, dict):
            continue
        companies.append(
            Company(
                name=str(item.get("name", "")).strip(),
                ticker=str(item.get("ticker", "")).strip(),
                sector=str(item.get("sector", "")).strip(),
                sector_label=str(item.get("sector_label", "")).strip(),
                material_topics=tuple(str(topic) for topic in item.get("material_topics", []) if topic),
                query_focus=tuple(str(query) for query in item.get("query_focus", []) if query),
                aliases=tuple(str(alias) for alias in item.get("aliases", []) if alias),
            )
        )
    return [company for company in companies if company.name and company.material_topics]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def humanize_topic(topic: str) -> str:
    text = topic.replace("E_and_S", "E&S").replace("P_C", "P&C")
    text = text.replace("M_and_A", "M&A").replace("_", " ")
    return normalize_text(text)


def stable_index(seed: str, length: int) -> int:
    if length <= 0:
        raise ValueError("cannot choose from an empty sequence")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % length


def load_gbrain_fixture(path: Path | None) -> tuple[bool, list[str], str | None]:
    if path is None:
        return False, [], None
    try:
        raw = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        return False, [], f"fixture_unavailable: {exc}"

    if isinstance(raw, dict):
        values = raw.get("threads") or raw.get("results") or raw.get("notes") or raw.get("signals") or []
    else:
        values = raw
    if not isinstance(values, list):
        return True, [], "fixture_has_no_list_results"

    texts: list[str] = []
    for item in values:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict):
            texts.append(" ".join(str(item.get(key) or "") for key in ("title", "slug", "summary", "body", "text", "content")))
    return True, [normalize_text(text) for text in texts if normalize_text(text)], None


def query_gbrain(timeout_seconds: int = 6) -> tuple[bool, list[str], str | None]:
    """Return read-only Gbrain search snippets, degrading quietly on failure."""

    snippets: list[str] = []
    gbrain_path = shutil_which("gbrain")
    if not gbrain_path:
        return False, [], "gbrain_cli_not_found"

    env = os.environ.copy()
    db_url_path = Path("~/.gbrain/database_url").expanduser()
    if not env.get("GBRAIN_DATABASE_URL") and db_url_path.exists():
        try:
            env["GBRAIN_DATABASE_URL"] = db_url_path.read_text(encoding="utf-8").strip()
        except OSError:
            pass

    for query in DEFAULT_GBRAIN_QUERIES:
        try:
            completed = subprocess.run(
                [gbrain_path, "search", query],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
                env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, snippets, f"gbrain_search_failed: {exc}"
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        for line in output.splitlines():
            clean = normalize_text(line)
            if clean and "No results" not in clean and not clean.startswith("[ai.gateway]"):
                snippets.append(clean)
    return True, dedupe(snippets)[:12], None


def shutil_which(command: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / command
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def company_score(company: Company, snippets: list[str]) -> int:
    haystack = "\n".join(snippets).lower()
    if not haystack:
        return 0
    names = (company.name, company.ticker, *company.aliases)
    score = sum(4 for name in names if name and name.lower() in haystack)
    score += sum(2 for topic in company.material_topics if humanize_topic(topic).lower() in haystack)
    score += sum(1 for token in company.sector_label.lower().replace("&", " ").split() if token in haystack)
    return score


def select_company(companies: list[Company], snippets: list[str], seed_date: date) -> tuple[Company, str]:
    scored = [(company_score(company, snippets), company) for company in companies]
    scored.sort(key=lambda item: (-item[0], item[1].name))
    if scored and scored[0][0] > 0:
        return scored[0][1], GBRAIN_SOURCE
    return companies[stable_index(f"{JOB_NAME}:{seed_date.isoformat()}", len(companies))], FALLBACK_SOURCE


def select_topic(company: Company, snippets: list[str], seed_date: date) -> str:
    haystack = "\n".join(snippets).lower()
    for topic in company.material_topics:
        human = humanize_topic(topic)
        if human.lower() in haystack or topic.lower() in haystack:
            return human
    return humanize_topic(company.material_topics[stable_index(f"{company.ticker}:{seed_date.isoformat()}", len(company.material_topics))])


def sector_angle(company: Company) -> str:
    if company.sector == "logistics":
        return "pricing, volume, service quality, and network-density data"
    if company.sector == "insurance_broking":
        return "organic growth, retention, rate environment, producer productivity, and fiduciary-income data"
    if company.sector == "tic":
        return "organic growth, regulation, outsourcing demand, utilization, and margin data"
    return "unit economics, customer behavior, competitive position, and management commentary"


def build_question(company: Company, topic: str) -> str:
    return (
        f"For {company.name}, what evidence from the latest filings, transcript, peer commentary, and {sector_angle(company)} would show whether {topic} is becoming a durable earnings driver rather than a one-period narrative?"
    )


def sentence_count(text: str) -> int:
    parts = re.split(r"(?<=[!?])\s+|(?<=[a-z0-9])\.\s+", text)
    return len([part for part in parts if part.strip()])


def validate_question(question: str, company: Company) -> list[str]:
    errors: list[str] = []
    lowered = question.lower()
    if not question.endswith("?"):
        errors.append("question must end with ?")
    if sentence_count(question) > 2:
        errors.append("question exceeds 2 sentences")
    if company.name.lower() not in lowered:
        errors.append("question is not anchored to the selected company")
    if any(term in lowered for term in GENERIC_MARKET_TERMS):
        errors.append("question contains generic macro/market-regime language")
    research_terms = ("evidence", "filings", "transcript", "data", "commentary")
    if not any(term in lowered for term in research_terms):
        errors.append("question does not name researchable evidence")
    return errors


def build_payload(
    *,
    dry_run: bool = False,
    generated_at: datetime | None = None,
    watchlist_path: Path | None = None,
    gbrain_fixture: Path | None = None,
) -> dict[str, Any]:
    emitted_at = generated_at or datetime.now(timezone.utc)
    companies = load_watchlist(watchlist_path)
    if not companies:
        raise ValueError("watchlist contains no usable companies")

    if gbrain_fixture is not None:
        gbrain_available, snippets, gbrain_error = load_gbrain_fixture(gbrain_fixture)
    else:
        gbrain_available, snippets, gbrain_error = query_gbrain()

    company, source = select_company(companies, snippets, emitted_at.date())
    topic = select_topic(company, snippets, emitted_at.date())
    question = build_question(company, topic)
    errors = validate_question(question, company)
    if errors:
        raise ValueError("; ".join(errors))

    return {
        "job": JOB_NAME,
        "generated_at": emitted_at.isoformat(),
        "dry_run": dry_run,
        "question": question,
        "source": source,
        "gbrain_available": gbrain_available,
        "gbrain_error": gbrain_error,
        "gbrain_snippet_count": len(snippets),
        "gbrain_writes": False,
        "kanban_mutations": False,
        "company": {
            "name": company.name,
            "ticker": company.ticker,
            "sector": company.sector,
            "sector_label": company.sector_label,
        },
        "material_topic": topic,
        "researchable_evidence": ["filings", "earnings transcript", "peer commentary", "sector operating data"],
    }


def format_plain(payload: dict[str, Any]) -> str:
    prefix = "[DRY RUN] " if payload["dry_run"] else ""
    return f"{prefix}{payload['question']}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one weekday investment research question")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writes")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit structured JSON")
    parser.add_argument("--watchlist-path", type=Path, help="Override source-controlled watchlist path")
    parser.add_argument(
        "--gbrain-json",
        type=Path,
        help="Optional test/runtime fixture for active Gbrain thread snippets; avoids calling the gbrain CLI.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_payload(
            dry_run=args.dry_run,
            watchlist_path=args.watchlist_path,
            gbrain_fixture=args.gbrain_json,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(format_plain(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
