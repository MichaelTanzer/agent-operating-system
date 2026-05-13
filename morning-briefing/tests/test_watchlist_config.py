from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "morning-briefing" / "config"
WATCHLIST_PATH = CONFIG_DIR / "watchlist.yaml"
SOURCE_RUBRIC_PATH = CONFIG_DIR / "source_rubric.yaml"


REQUIRED_COMPANY_FIELDS = {
    "name",
    "ticker",
    "exchange",
    "sector",
    "sector_label",
    "aliases",
    "material_topics",
    "query_focus",
    "noise_exclusions",
}


EXPECTED_COMPANIES = {
    "Aon",
    "ArcBest",
    "Arthur J. Gallagher",
    "Brown & Brown",
    "Bureau Veritas",
    "C.H. Robinson",
    "DSV",
    "Eurofins Scientific",
    "Forward Air",
    "GXO Logistics",
    "Intertek Group",
    "Kuehne+Nagel",
    "Mainfreight",
    "Marsh McLennan",
    "Old Dominion Freight Line",
    "RXO",
    "Ryan Specialty",
    "Saia",
    "SGS",
    "Baldwin Insurance Group",
    "UL Solutions",
    "WTW",
    "XPO",
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_watchlist_preserves_exact_approved_company_count() -> None:
    watchlist = load_yaml(WATCHLIST_PATH)
    companies = watchlist["companies"]

    assert watchlist["approved_company_count"] == 23
    assert len(companies) == 23
    assert {company["name"] for company in companies} == EXPECTED_COMPANIES


def test_each_company_has_aliases_material_topics_queries_and_noise_filters() -> None:
    watchlist = load_yaml(WATCHLIST_PATH)

    for company in watchlist["companies"]:
        assert REQUIRED_COMPANY_FIELDS <= company.keys(), company["name"]
        assert company["sector"] in {"logistics", "insurance_broking", "tic"}
        assert len(company["aliases"]) >= 3, company["name"]
        assert len(company["material_topics"]) >= 5, company["name"]
        assert len(company["query_focus"]) >= 3, company["name"]
        assert len(company["noise_exclusions"]) >= 2, company["name"]


def test_watchlist_links_to_source_rubric_and_has_query_taxonomy() -> None:
    watchlist = load_yaml(WATCHLIST_PATH)

    assert watchlist["source_rubric_path"] == "morning-briefing/config/source_rubric.yaml"
    assert watchlist["source_quality_taxonomy"]["source_rubric_path"] == watchlist["source_rubric_path"]
    assert set(watchlist["sectors"]) == {"logistics", "insurance_broking", "tic"}
    assert set(watchlist["consulting_white_paper_query_patterns"]) == {
        "global",
        "logistics",
        "insurance_broking",
        "tic",
    }
    assert len(watchlist["low_quality_noise_exclusions"]) >= 10


def test_source_rubric_defines_ranking_materiality_and_noise_exclusions() -> None:
    rubric = load_yaml(SOURCE_RUBRIC_PATH)

    assert list(rubric["source_tiers"]) == [
        "tier1_primary",
        "tier2_verified_business_press",
        "tier3_expert_research_and_white_papers",
        "tier4_specialist_blogs_and_newsletters",
        "tier5_low_quality_or_noise",
    ]
    assert rubric["source_tiers"]["tier1_primary"]["rank"] == 1
    assert rubric["source_tiers"]["tier5_low_quality_or_noise"]["default_action"] == "exclude"
    assert "consulting_white_papers" in rubric["query_patterns"]
    assert "global" in rubric["noise_exclusions"]
    assert rubric["scoring"]["include_threshold"] > rubric["scoring"]["exclude_below"]
