#!/usr/bin/env python3
"""
watchlist_digest.py — Weekday company + industry watchlist digest prototype.

The BR-015R prototype is intentionally deterministic and local-first: it loads
BR-014's approved 23-company taxonomy, collects candidate items from either a
JSON file or a small built-in prototype feed, dedupes/filter-noises the feed,
scores materiality with source_rubric.yaml, and renders only material items with
links and "why it matters" notes.

Dry-run:
    python3 morning-briefing/scripts/watchlist_digest.py --dry-run
    python3 morning-briefing/scripts/watchlist_digest.py --dry-run --json
    python3 morning-briefing/scripts/watchlist_digest.py --dry-run --company AON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by operator environment
    print("ERROR: PyYAML not installed. Run: uvx --with pyyaml python ...", file=sys.stderr)
    sys.exit(1)


JOB_NAME = "company_watchlist"
MAX_DIGEST_ITEMS = 10
WATCHLIST_RELATIVE_PATH = Path("morning-briefing/config/watchlist.yaml")


@dataclass(frozen=True)
class Candidate:
    title: str
    source: str
    source_tier: str
    url: str
    published_at: str
    summary: str
    matched_tickers: tuple[str, ...] = ()
    matched_companies: tuple[str, ...] = ()
    materiality_signals: tuple[str, ...] = ()
    industry_signal: bool = False
    consulting_signal: bool = False
    primary_data: bool = False
    corroborated: bool = False
    sponsored: bool = False


@dataclass
class ScoredCandidate:
    candidate: Candidate
    score: int
    status: str
    score_reasons: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    matched_material_topics: list[str] = field(default_factory=list)
    companies: list[dict[str, Any]] = field(default_factory=list)


PROTOTYPE_CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        title="Aon highlights treaty-renewal pricing, Risk Capital integration, and margin program in investor update",
        source="Aon Investor Relations",
        source_tier="tier1_primary",
        url="https://www.aon.com/investors/",
        published_at="2026-05-12",
        summary=(
            "Official investor materials discuss reinsurance treaty renewal pricing, "
            "Risk Capital integration, and restructuring benefits that can alter "
            "organic growth and margin trajectory."
        ),
        matched_tickers=("AON",),
        matched_companies=("Aon",),
        materiality_signals=("pricing_power", "integration_execution", "margin_structure"),
        primary_data=True,
    ),
    Candidate(
        title="Consulting outlook: casualty severity keeps commercial insurance pricing and broker advisory demand elevated",
        source="Deloitte Insurance Outlook",
        source_tier="tier3_expert_research_and_white_papers",
        url="https://www.deloitte.com/global/en/Industries/financial-services/insurance.html",
        published_at="2026-05-12",
        summary=(
            "A consulting-sector outlook frames casualty loss-cost inflation, analytics, "
            "and risk-advisory demand as durable industry drivers for insurance brokers."
        ),
        matched_tickers=("AON", "MMC", "WTW", "AJG", "BRO", "RYAN"),
        matched_companies=(
            "Aon",
            "Marsh McLennan",
            "Willis Towers Watson",
            "Arthur J. Gallagher",
            "Brown & Brown",
            "Ryan Specialty",
        ),
        materiality_signals=(
            "underwriting_cycle_or_insurance_market_hardness",
            "customer_mix_or_end_market_change",
            "pricing_power",
        ),
        industry_signal=True,
        consulting_signal=True,
        primary_data=True,
    ),
    Candidate(
        title="Old Dominion Freight Line adds service-center capacity while preserving LTL yield discipline",
        source="FreightWaves",
        source_tier="tier2_verified_business_press",
        url="https://www.freightwaves.com/news/old-dominion-freight-line",
        published_at="2026-05-11",
        summary=(
            "Trade reporting ties network capacity additions to shipment density, service "
            "quality, and LTL yield discipline rather than a one-day freight-rate move."
        ),
        matched_tickers=("ODFL",),
        matched_companies=("Old Dominion Freight Line",),
        materiality_signals=("capacity_or_network_change", "pricing_power", "organic_growth_or_share_gain"),
        corroborated=True,
    ),
    Candidate(
        title="TIC Council note: PFAS and battery standards expand testing, inspection, and certification demand",
        source="TIC Council",
        source_tier="tier2_verified_business_press",
        url="https://www.tic-council.org/",
        published_at="2026-05-10",
        summary=(
            "Industry-association signal points to standards-led demand for laboratories, "
            "product assurance, and compliance outsourcing across TIC operators."
        ),
        matched_tickers=("BVI.PA", "ERF.PA", "ITRK.L", "SGSOY"),
        matched_companies=("Bureau Veritas", "Eurofins Scientific", "Intertek", "SGS"),
        materiality_signals=("regulatory_or_compliance_change", "safety_or_certification_regime_change"),
        industry_signal=True,
        primary_data=True,
    ),
    Candidate(
        title="C.H. Robinson stock rose today after analyst price target change",
        source="MarketBeat",
        source_tier="tier5_low_quality_or_noise",
        url="https://www.marketbeat.com/",
        published_at="2026-05-12",
        summary="Automated market recap with no company-specific operating facts.",
        matched_tickers=("CHRW",),
        matched_companies=("C.H. Robinson",),
        materiality_signals=("daily_stock_move", "analyst_price_target_change"),
    ),
    Candidate(
        title="Generic freight market size to grow with AI blockchain logistics platforms",
        source="Sponsored vendor blog",
        source_tier="tier5_low_quality_or_noise",
        url="https://example.com/sponsored-freight-ai",
        published_at="2026-05-12",
        summary="Sponsored listicle with no named watchlist company or primary data.",
        materiality_signals=("undifferentiated_market_size_forecast",),
        industry_signal=True,
        sponsored=True,
    ),
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "morning-briefing" / "config" / "watchlist.yaml").exists():
            return ancestor
    return Path.cwd()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def resolve_watchlist_path(path_arg: Path | None = None) -> Path:
    if path_arg:
        path = path_arg.expanduser()
        return path if path.is_absolute() else repo_root() / path
    return repo_root() / WATCHLIST_RELATIVE_PATH


def load_taxonomy(watchlist_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    watchlist = load_yaml(watchlist_path)
    rubric_path = repo_root() / watchlist.get("source_rubric_path", "morning-briefing/config/source_rubric.yaml")
    rubric = load_yaml(rubric_path)
    return watchlist, rubric


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def tokens_for_topic(topic: str) -> set[str]:
    return {token for token in re.split(r"[_\W]+", topic.lower()) if len(token) > 2}


def candidate_from_dict(raw: dict[str, Any]) -> Candidate:
    def tuple_field(name: str) -> tuple[str, ...]:
        value = raw.get(name, ())
        if isinstance(value, str):
            return (value,)
        return tuple(str(item) for item in value)

    return Candidate(
        title=str(raw["title"]),
        source=str(raw.get("source", "Unknown source")),
        source_tier=str(raw.get("source_tier", "tier5_low_quality_or_noise")),
        url=str(raw.get("url", "")),
        published_at=str(raw.get("published_at", "")),
        summary=str(raw.get("summary", "")),
        matched_tickers=tuple_field("matched_tickers"),
        matched_companies=tuple_field("matched_companies"),
        materiality_signals=tuple_field("materiality_signals"),
        industry_signal=bool(raw.get("industry_signal", False)),
        consulting_signal=bool(raw.get("consulting_signal", False)),
        primary_data=bool(raw.get("primary_data", False)),
        corroborated=bool(raw.get("corroborated", False)),
        sponsored=bool(raw.get("sponsored", False)),
    )


def collect_candidates(input_path: Path | None = None) -> list[Candidate]:
    if not input_path:
        return list(PROTOTYPE_CANDIDATES)

    with input_path.expanduser().open(encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("candidates", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("candidate input must be a JSON list or {'candidates': [...]} object")
    return [candidate_from_dict(row) for row in rows]


def company_index(companies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for company in companies:
        names = [company["name"], company["ticker"], *company.get("aliases", [])]
        for name in names:
            index[normalize_text(str(name))] = company
    return index


def matched_companies(candidate: Candidate, companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ticker_map = {str(company["ticker"]).upper(): company for company in companies}
    name_map = {normalize_text(str(company["name"])): company for company in companies}
    matched: dict[str, dict[str, Any]] = {}

    for ticker in candidate.matched_tickers:
        company = ticker_map.get(ticker.upper())
        if company:
            matched[company["ticker"]] = company
    for name in candidate.matched_companies:
        company = name_map.get(normalize_text(name))
        if company:
            matched[company["ticker"]] = company

    haystack = normalize_text(f"{candidate.title} {candidate.summary}")
    aliases = company_index(companies)
    for alias, company in aliases.items():
        if alias and re.search(rf"\b{re.escape(alias)}\b", haystack):
            matched[company["ticker"]] = company

    return list(matched.values())


def is_noise(candidate: Candidate, rubric: dict[str, Any], companies: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    haystack = normalize_text(f"{candidate.title} {candidate.summary} {candidate.source}")
    reasons: list[str] = []
    noise = rubric.get("noise_exclusions", {})
    phrases: list[str] = []
    phrases.extend(noise.get("global", []))
    for company in companies:
        phrases.extend(company.get("noise_exclusions", []))
        sector_noise = noise.get(company.get("sector", ""), [])
        phrases.extend(sector_noise)

    for phrase in phrases:
        phrase_norm = normalize_text(str(phrase))
        if phrase_norm and phrase_norm in haystack:
            reasons.append(str(phrase))

    excluded_signals = set(rubric.get("materiality_signals", {}).get("exclude_unless_extreme", []))
    if candidate.materiality_signals and set(candidate.materiality_signals).issubset(excluded_signals):
        reasons.append("only exclude-unless-extreme materiality signals present")

    if candidate.source_tier == "tier5_low_quality_or_noise":
        reasons.append("tier5 low-quality/noise source")
    if candidate.sponsored:
        reasons.append("sponsored/vendor-only source")

    return bool(reasons), reasons


def score_candidate(candidate: Candidate, rubric: dict[str, Any], companies: list[dict[str, Any]]) -> ScoredCandidate:
    scoring = rubric.get("scoring", {})
    score = int(scoring.get("base_points_by_tier", {}).get(candidate.source_tier, 0))
    reasons = [f"base {score} from {candidate.source_tier}"]
    penalties: list[str] = []
    matched_topics: list[str] = []
    boosts = scoring.get("boosts", {})
    penalty_values = scoring.get("penalties", {})
    include_signals = set(rubric.get("materiality_signals", {}).get("include", []))

    if companies:
        score += int(boosts.get("company_named", 0))
        reasons.append("company_named")
    if candidate.matched_tickers:
        score += int(boosts.get("ticker_named_with_context", 0))
        reasons.append("ticker_named_with_context")
    if candidate.primary_data:
        score += int(boosts.get("primary_data_or_original_research", 0))
        reasons.append("primary_data_or_original_research")
    if candidate.corroborated:
        score += int(boosts.get("multi_source_corroboration", 0))
        reasons.append("multi_source_corroboration")

    if any(signal in include_signals for signal in candidate.materiality_signals):
        score += int(boosts.get("long_term_economics_signal", 0))
        reasons.append("long_term_economics_signal")

    haystack_tokens = set(normalize_text(f"{candidate.title} {candidate.summary}").split())
    for company in companies:
        for topic in company.get("material_topics", []):
            topic_tokens = tokens_for_topic(str(topic))
            if topic_tokens and topic_tokens & haystack_tokens:
                matched_topics.append(str(topic))
    if matched_topics:
        score += int(boosts.get("material_topic_match", 0))
        reasons.append("material_topic_match")

    if "daily_stock_move" in candidate.materiality_signals or "stock rose" in normalize_text(candidate.title):
        value = int(penalty_values.get("stock_price_only", 0))
        score += value
        penalties.append("stock_price_only")
    if candidate.sponsored:
        value = int(penalty_values.get("sponsored_or_vendor_only", 0))
        score += value
        penalties.append("sponsored_or_vendor_only")
    if not candidate.source or candidate.source == "Unknown source":
        value = int(penalty_values.get("no_named_source_or_author", 0))
        score += value
        penalties.append("no_named_source_or_author")

    is_noisy, noise_reasons = is_noise(candidate, rubric, companies)
    penalties.extend(noise_reasons)

    include_threshold = int(scoring.get("include_threshold", 6))
    context_threshold = int(scoring.get("context_threshold", 4))
    if is_noisy or score < context_threshold:
        status = "excluded"
    elif score >= include_threshold:
        status = "include"
    else:
        status = "context"

    return ScoredCandidate(
        candidate=candidate,
        score=score,
        status=status,
        score_reasons=reasons,
        penalties=penalties,
        matched_material_topics=sorted(set(matched_topics)),
        companies=companies,
    )


def dedupe(candidates: Iterable[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    unique: list[Candidate] = []
    for candidate in candidates:
        key = normalize_text(candidate.url or candidate.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def checked_companies(watchlist: dict[str, Any], company_filter: str | None = None) -> list[dict[str, Any]]:
    companies = watchlist.get("companies", [])
    if not company_filter:
        return list(companies)
    needle = company_filter.upper()
    return [
        company for company in companies
        if str(company.get("ticker", "")).upper() == needle
        or normalize_text(str(company.get("name", ""))) == normalize_text(company_filter)
    ]


def candidate_to_payload(scored: ScoredCandidate) -> dict[str, Any]:
    candidate = scored.candidate
    companies = [
        {
            "name": company["name"],
            "ticker": company["ticker"],
            "sector": company["sector"],
        }
        for company in scored.companies
    ]
    labels = [f"{company['name']} ({company['ticker']})" for company in companies]
    if candidate.industry_signal and not labels:
        labels.append("Industry-wide")
    why_parts = []
    if candidate.consulting_signal:
        why_parts.append("consulting/industry signal")
    if candidate.industry_signal:
        why_parts.append("sector read-through")
    if candidate.materiality_signals:
        why_parts.append(", ".join(candidate.materiality_signals[:3]))
    why = "; ".join(why_parts) or "material long-term company trajectory signal"

    return {
        "companies": companies,
        "company": ", ".join(labels),
        "ticker": ", ".join(company["ticker"] for company in companies),
        "headline": candidate.title,
        "source": candidate.source,
        "source_tier": candidate.source_tier,
        "url": candidate.url,
        "published_at": candidate.published_at,
        "materiality_signal": list(candidate.materiality_signals),
        "score": scored.score,
        "why_it_matters": f"{why}. {candidate.summary}",
        "industry_signal": candidate.industry_signal,
        "consulting_signal": candidate.consulting_signal,
        "matched_material_topics": scored.matched_material_topics,
    }


def build_payload(
    *,
    dry_run: bool,
    company: str | None = None,
    input_candidates: Path | None = None,
    generated_at: datetime | None = None,
    watchlist_path: Path | None = None,
) -> dict[str, Any]:
    resolved_watchlist_path = resolve_watchlist_path(watchlist_path)
    watchlist, rubric = load_taxonomy(resolved_watchlist_path)
    approved_count = int(watchlist.get("approved_company_count", 0))
    checked = checked_companies(watchlist, company)
    candidates = dedupe(collect_candidates(input_candidates))

    scored: list[ScoredCandidate] = []
    for candidate in candidates:
        companies = matched_companies(candidate, checked)
        if company and not companies:
            continue
        if not company and not companies and not candidate.industry_signal:
            continue
        scored.append(score_candidate(candidate, rubric, companies))

    material = [item for item in scored if item.status == "include"]
    material.sort(key=lambda item: (item.score, item.candidate.source_tier), reverse=True)
    digest_items = [candidate_to_payload(item) for item in material[:MAX_DIGEST_ITEMS]]
    context_items = [candidate_to_payload(item) for item in scored if item.status == "context"]
    excluded_count = sum(1 for item in scored if item.status == "excluded")

    coverage_note = (
        f"Checked {len(checked)}/{approved_count} approved companies"
        f" ({', '.join(company['ticker'] for company in checked)}). "
        f"Reviewed {len(candidates)} candidates after dedupe; surfaced {len(digest_items)} material item(s) "
        f"and excluded {excluded_count} noise/low-materiality item(s)."
    )

    return {
        "job": JOB_NAME,
        "generated_at": (generated_at or datetime.now(timezone.utc)).isoformat(),
        "dry_run": dry_run,
        "watchlist_path": str(resolved_watchlist_path),
        "approved_company_count": approved_count,
        "checked_company_count": len(checked),
        "checked_companies": [
            {"name": item["name"], "ticker": item["ticker"], "sector": item["sector"]}
            for item in checked
        ],
        "candidate_count": len(candidates),
        "deduped_candidate_count": len(candidates),
        "material_item_count": len(digest_items),
        "items": digest_items,
        "context_items": context_items,
        "coverage_note": coverage_note,
        "consulting_industry_signal_included": any(
            item["consulting_signal"] or item["industry_signal"]
            for item in [*digest_items, *context_items]
        ),
        "max_items": MAX_DIGEST_ITEMS,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("approved_company_count") != 23:
        errors.append("approved_company_count must be exactly 23")
    if not payload.get("items"):
        errors.append("expected at least one material digest item")
    if len(payload.get("items", [])) > payload.get("max_items", MAX_DIGEST_ITEMS):
        errors.append("too many digest items")
    if payload.get("checked_company_count") != len(payload.get("checked_companies", [])):
        errors.append("checked_company_count does not match checked_companies")
    if not payload.get("coverage_note"):
        errors.append("coverage_note is required")
    if not payload.get("consulting_industry_signal_included"):
        errors.append("expected consulting/industry signal")
    for item in payload.get("items", []):
        for field_name in ("headline", "source_tier", "url", "why_it_matters"):
            if not item.get(field_name):
                errors.append(f"item missing {field_name}: {item}")
    return errors


def render_plain(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    if payload["dry_run"]:
        lines.append("[DRY RUN] watchlist_digest.py")
    lines.append("Company + Industry Watchlist Digest")
    lines.append(payload["coverage_note"])

    if not payload["items"]:
        lines.append("")
        lines.append("No material watchlist items cleared the threshold today.")
        return "\n".join(lines)

    for item in payload["items"]:
        lines.append("")
        lines.append(f"- {item['company']}: {item['headline']}")
        lines.append(f"  Source: {item['source']} ({item['source_tier']}) — {item['url']}")
        lines.append(f"  Materiality: {', '.join(item['materiality_signal'])}")
        lines.append(f"  Why it matters: {item['why_it_matters']}")

    context_items = payload.get("context_items", [])
    if context_items:
        lines.append("")
        lines.append("Context watch (below headline threshold):")
        for item in context_items:
            lines.append(f"- {item['headline']} — {item['source']} ({item['source_tier']})")

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekday company + industry watchlist digest")
    parser.add_argument("--dry-run", action="store_true", help="Preview digest without runtime writes")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    parser.add_argument("--company", help="Limit manual run to a single ticker or company name")
    parser.add_argument("--watchlist-path", type=Path, help="Override watchlist.yaml path")
    parser.add_argument(
        "--input-candidates",
        type=Path,
        help="Optional JSON list of externally collected candidates for scoring",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = build_payload(
            dry_run=args.dry_run,
            company=args.company,
            input_candidates=args.input_candidates,
            watchlist_path=args.watchlist_path,
        )
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_plain(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
