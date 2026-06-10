"""
LangGraph Workflow - Orchestrates the agent pipeline.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional, Annotated
from operator import add
from loguru import logger

from langgraph.graph import StateGraph, END

from agents.search_agent import SearchAgent
from agents.crawl_agent import CrawlAgent
from agents.extraction_agent import ExtractionAgent
from agents.relevance_agent import RelevanceAgent
from agents.classification_agent import ClassificationAgent
from agents.college_agent import CollegeMatchingAgent
from agents.dedup_agent import DeduplicationAgent
from agents.scoring_agent import ScoringAgent
from config.settings import settings


class ResourceDiscoveryState(TypedDict):
    """State for the resource discovery workflow."""
    # Input
    course_code: str
    course_name: str
    college_id: Optional[int]
    college_name: Optional[str]  # Added for college-specific search
    
    # Pipeline data
    search_results: List[Dict[str, Any]]
    crawled_results: List[Dict[str, Any]]
    extracted_results: List[Dict[str, Any]]
    relevant_results: List[Dict[str, Any]]
    classified_results: List[Dict[str, Any]]
    college_matched_results: List[Dict[str, Any]]
    deduped_results: List[Dict[str, Any]]
    scored_results: List[Dict[str, Any]]
    
    # Output
    final_resources: List[Dict[str, Any]]
    
    # Metadata
    job_id: str
    errors: List[str]
    stats: Dict[str, int]


def create_initial_state(
    course_code: str,
    course_name: str,
    college_id: Optional[int] = None,
    college_name: Optional[str] = None,
) -> ResourceDiscoveryState:
    """Create initial state for workflow."""
    return ResourceDiscoveryState(
        course_code=course_code,
        course_name=course_name,
        college_id=college_id,
        college_name=college_name,
        search_results=[],
        crawled_results=[],
        extracted_results=[],
        relevant_results=[],
        classified_results=[],
        college_matched_results=[],
        deduped_results=[],
        scored_results=[],
        final_resources=[],
        job_id=str(uuid.uuid4()),
        errors=[],
        stats={
            "searched": 0,
            "crawled": 0,
            "extracted": 0,
            "relevant": 0,
            "classified": 0,
            "matched": 0,
            "deduped": 0,
            "scored": 0,
            "final": 0,
        },
    )


# Node functions
def search_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Search for resources."""
    logger.info(f"Searching for: {state['course_code']} - {state['course_name']}")
    
    agent = SearchAgent()
    results = agent.search_for_course(
        state["course_code"],
        state["course_name"],
        max(settings.crawler_max_results_per_query, 25),
        state.get("college_name"),  # Pass college name for targeted search
    )
    
    return {
        "search_results": results,
        "stats": {**state["stats"], "searched": len(results)},
    }


def _is_pdf_like(item: Dict[str, Any]) -> bool:
    url = (item.get("url") or "").lower()
    title = (item.get("title") or "").lower()
    file_type = (item.get("file_type") or "").lower()
    return (
        file_type == "pdf"
        or url.endswith(".pdf")
        or ".pdf" in url
        or "pdf" in title
    )


def crawl_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Crawl search results."""
    logger.info(f"Crawling {len(state['search_results'])} URLs")
    
    agent = CrawlAgent()
    results = []
    
    for item in state["search_results"][: settings.crawler_max_urls_per_run]:
        url = item.get("link", "")
        if url:
            crawl_result = agent.crawl(url)
            crawl_result["search_data"] = item
            results.append(crawl_result)
    
    return {
        "crawled_results": results,
        "stats": {**state["stats"], "crawled": len(results)},
    }


def extract_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Extract and structure content."""
    logger.info(f"Extracting from {len(state['crawled_results'])} pages")
    
    agent = ExtractionAgent()
    results = []
    
    for item in state["crawled_results"]:
        extracted = agent.extract(item)
        if extracted.get("valid"):
            extracted["search_data"] = item.get("search_data", {})
            results.append(extracted)
    
    return {
        "extracted_results": results,
        "stats": {**state["stats"], "extracted": len(results)},
    }


def relevance_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Check relevance of resources."""
    logger.info(f"Checking relevance of {len(state['extracted_results'])} resources")
    
    agent = RelevanceAgent()
    results = []
    
    for item in state["extracted_results"]:
        relevance = agent.evaluate(
            state["course_code"],
            state["course_name"],
            item.get("title", ""),
            item.get("content_snippet", ""),
            item.get("url", ""),
        )
        
        if relevance.get("is_relevant"):
            item["relevance"] = relevance
            results.append(item)
    
    return {
        "relevant_results": results,
        "stats": {**state["stats"], "relevant": len(results)},
    }


def classify_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Classify resource types."""
    logger.info(f"Classifying {len(state['relevant_results'])} resources")
    
    agent = ClassificationAgent()
    results = []
    
    for item in state["relevant_results"]:
        classification = agent.classify(
            item.get("title", ""),
            item.get("content_snippet", ""),
            item.get("detected_keywords", []),
        )
        item["classification"] = classification
        results.append(item)
    
    return {
        "classified_results": results,
        "stats": {**state["stats"], "classified": len(results)},
    }


def college_match_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Match resources to colleges."""
    logger.info(f"Matching colleges for {len(state['classified_results'])} resources")
    
    agent = CollegeMatchingAgent()
    results = []
    target_college = state.get("college_name")
    
    for item in state["classified_results"]:
        match = agent.match(
            item.get("url", ""),
            item.get("full_content", ""),
            item.get("title", ""),
        )
        if (
            target_college
            and settings.crawler_enforce_requested_college
            and not agent.matches_target_college(match, target_college)
        ):
            continue
        item["college_match"] = match
        results.append(item)
    
    return {
        "college_matched_results": results,
        "stats": {**state["stats"], "matched": len(results)},
    }


def dedup_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Deduplicate resources."""
    logger.info(f"Deduplicating {len(state['college_matched_results'])} resources")
    
    agent = DeduplicationAgent()
    results = []
    
    for item in state["college_matched_results"]:
        dedup = agent.check_duplicate(
            item.get("url", ""),
            item.get("full_content", ""),
        )
        
        if not dedup.get("is_duplicate"):
            item["dedup"] = dedup
            results.append(item)
    
    return {
        "deduped_results": results,
        "stats": {**state["stats"], "deduped": len(results)},
    }


def score_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Score resources."""
    logger.info(f"Scoring {len(state['deduped_results'])} resources")
    
    agent = ScoringAgent()
    results = []
    
    for item in state["deduped_results"]:
        from utils.helpers import extract_domain
        
        score = agent.score(
            item.get("relevance", {}).get("confidence_score", 0),
            item.get("classification", {}).get("confidence", 0),
            item.get("college_match", {}).get("confidence", 0),
            extract_domain(item.get("url", "")),
            college_required=bool(
                state.get("college_name") and settings.crawler_enforce_requested_college
            ),
        )
        item["score"] = score
        results.append(item)
    
    return {
        "scored_results": results,
        "stats": {**state["stats"], "scored": len(results)},
    }


def filter_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Filter resources by threshold and prepare final output."""
    logger.info(f"Filtering {len(state['scored_results'])} resources")
    
    final_resources = []
    
    for item in state["scored_results"]:
        if item.get("score", {}).get("passes_threshold", False):
            if not settings.crawler_accept_non_pdf_resources and not _is_pdf_like(item):
                continue
            from utils.helpers import extract_domain
            
            resource = {
                "title": item.get("title", ""),
                "file_url": item.get("url", ""),
                "source_domain": extract_domain(item.get("url", "")),
                "content_snippet": item.get("content_snippet", ""),
                "resource_type": item.get("classification", {}).get("resource_type", "other"),
                "file_type": item.get("file_type", "html"),
                "course_code": state["course_code"],
                "course_name": state["course_name"],
                "college_name": item.get("college_match", {}).get("college_name"),
                "relevance_score": item.get("relevance", {}).get("confidence_score", 0),
                "type_confidence": item.get("classification", {}).get("confidence", 0),
                "college_confidence": item.get("college_match", {}).get("confidence", 0),
                "domain_trust_score": item.get("score", {}).get("domain_trust_score", 1.0),
                "final_score": item.get("score", {}).get("final_score", 0),
                "ai_confidence": item.get("relevance", {}).get("confidence_score", 0),
                "relevance_reason": item.get("relevance", {}).get("reason", ""),
                "quality_indicators": item.get("relevance", {}).get("quality_indicators", []),
                "score_breakdown": item.get("score", {}).get("score_breakdown", {}),
                "source": item.get("search_data", {}).get("source", ""),
                "search_query": item.get("search_data", {}).get("search_query", ""),
                "candidate_score": item.get("search_data", {}).get("candidate_score", 0),
                "url_hash": item.get("dedup", {}).get("url_hash", ""),
                "content_hash": item.get("dedup", {}).get("content_hash", ""),
                "detected_keywords": item.get("keyword_json", "[]"),
                "crawled_at": datetime.utcnow().isoformat(),
            }
            final_resources.append(resource)
    
    # Sort by score
    final_resources.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return {
        "final_resources": final_resources,
        "stats": {**state["stats"], "final": len(final_resources)},
    }


def build_workflow() -> StateGraph:
    """Build the LangGraph workflow."""
    workflow = StateGraph(ResourceDiscoveryState)
    
    # Add nodes
    workflow.add_node("search", search_node)
    workflow.add_node("crawl", crawl_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("relevance", relevance_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("college_match", college_match_node)
    workflow.add_node("dedup", dedup_node)
    workflow.add_node("score", score_node)
    workflow.add_node("filter", filter_node)
    
    # Add edges
    workflow.set_entry_point("search")
    workflow.add_edge("search", "crawl")
    workflow.add_edge("crawl", "extract")
    workflow.add_edge("extract", "relevance")
    workflow.add_edge("relevance", "classify")
    workflow.add_edge("classify", "college_match")
    workflow.add_edge("college_match", "dedup")
    workflow.add_edge("dedup", "score")
    workflow.add_edge("score", "filter")
    workflow.add_edge("filter", END)
    
    return workflow.compile()


# Global workflow instance
_workflow = None


def get_workflow():
    """Get or create workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def run_discovery_pipeline(
    course_code: str,
    course_name: str,
    college_id: Optional[int] = None,
    college_name: Optional[str] = None,
) -> ResourceDiscoveryState:
    """Run the full discovery pipeline for a course."""
    logger.info(f"Starting pipeline for: {course_code} - {course_name} (college: {college_name})")
    
    initial_state = create_initial_state(course_code, course_name, college_id, college_name)
    workflow = get_workflow()
    
    try:
        final_state = workflow.invoke(initial_state)
        logger.info(f"Pipeline complete. Found {len(final_state['final_resources'])} resources")
        return final_state
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        initial_state["errors"].append(str(e))
        return initial_state
