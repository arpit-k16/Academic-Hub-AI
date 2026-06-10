"""Agents package."""

from importlib import import_module

__all__ = [
    "run_discovery_pipeline",
    "ResourceDiscoveryState",
    "SearchAgent",
    "CrawlAgent",
    "ExtractionAgent",
    "RelevanceAgent",
    "ClassificationAgent",
    "CollegeMatchingAgent",
    "DeduplicationAgent",
    "ScoringAgent",
]

_EXPORTS = {
    "run_discovery_pipeline": ("agents.workflow", "run_discovery_pipeline"),
    "ResourceDiscoveryState": ("agents.workflow", "ResourceDiscoveryState"),
    "SearchAgent": ("agents.search_agent", "SearchAgent"),
    "CrawlAgent": ("agents.crawl_agent", "CrawlAgent"),
    "ExtractionAgent": ("agents.extraction_agent", "ExtractionAgent"),
    "RelevanceAgent": ("agents.relevance_agent", "RelevanceAgent"),
    "ClassificationAgent": ("agents.classification_agent", "ClassificationAgent"),
    "CollegeMatchingAgent": ("agents.college_agent", "CollegeMatchingAgent"),
    "DeduplicationAgent": ("agents.dedup_agent", "DeduplicationAgent"),
    "ScoringAgent": ("agents.scoring_agent", "ScoringAgent"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module 'agents' has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    return getattr(import_module(module_name), attr_name)
