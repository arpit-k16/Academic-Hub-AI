"""
Crawl API routes - triggers resource discovery pipeline.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from loguru import logger

from db.database import get_db
from db import crud
from agents.workflow import run_discovery_pipeline
from agents.college_agent import CollegeMatchingAgent
from config.settings import settings


router = APIRouter()


class DiscoverRequest(BaseModel):
    course_code: str
    course_name: str
    college_name: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "course_code": "CS101",
                "course_name": "Data Structures",
                "college_name": "Kalinga Institute of Industrial Technology"
            }
        }


class DiscoverResponse(BaseModel):
    status: str
    message: str
    resources_found: int
    resources_added: int
    high_confidence: int
    details: List[dict]


def process_discovery(
    course_code: str,
    course_name: str,
    college_name: Optional[str],
    db: Session
) -> dict:
    """Run the full discovery pipeline."""
    logger.info(f"Starting discovery for {course_code}: {course_name} at {college_name}")
    
    # Run the LangGraph pipeline with college name for targeted search
    result = run_discovery_pipeline(
        course_code=course_code,
        course_name=course_name,
        college_id=None,
        college_name=college_name,  # Pass for college-specific search
    )
    
    resources_added = 0
    high_confidence = 0
    details = []
    
    matcher = CollegeMatchingAgent()
    expected_domain = matcher.get_expected_domain(college_name or "")

    # Process results and save to database
    for resource in result.get("final_resources", []):
        try:
            # Optional enforcement for college-only or direct-PDF-only deployments.
            source_domain = (resource.get("source_domain") or "").lower()
            file_url = resource.get("file_url", "")
            if college_name and settings.crawler_enforce_requested_college:
                matched_college = resource.get("college_name") or ""
                if expected_domain and expected_domain not in source_domain:
                    details.append({
                        "url": file_url,
                        "status": "skipped",
                        "message": f"Not from requested college domain ({expected_domain})",
                    })
                    continue
                if not expected_domain and college_name.lower() not in matched_college.lower():
                    details.append({
                        "url": file_url,
                        "status": "skipped",
                        "message": "College did not match requested college",
                    })
                    continue
            if (
                not settings.crawler_accept_non_pdf_resources
                and ".pdf" not in file_url.lower()
                and resource.get("file_type", "").lower() != "pdf"
            ):
                details.append({
                    "url": file_url,
                    "status": "skipped",
                    "message": "Not a direct PDF resource",
                })
                continue

            # Check if already exists
            existing = crud.get_resource_by_url(db, file_url)
            if existing:
                details.append({
                    "url": file_url,
                    "status": "duplicate",
                    "message": "Already exists in database"
                })
                continue
            
            # Determine college_id
            college_id = None
            detected_college = resource.get("college_name") or college_name
            if detected_college:
                college = crud.get_or_create_college(db, detected_college, resource.get("source_domain"))
                college_id = college.id
            
            # Create resource
            from db.models import ResourceStatus, ResourceType
            
            resource_type_str = resource.get("resource_type", "notes").lower()
            resource_type_map = {
                "notes": ResourceType.NOTES,
                "question_paper": ResourceType.QUESTION_PAPER,
                "syllabus": ResourceType.SYLLABUS,
                "practical": ResourceType.PRACTICAL,
                "tutorial": ResourceType.TUTORIAL,
                "reference": ResourceType.REFERENCE,
                "other": ResourceType.OTHER,
            }
            resource_type = resource_type_map.get(resource_type_str, ResourceType.OTHER)
            
            new_resource = crud.create_resource(
                db,
                title=resource.get("title", "Untitled"),
                file_url=resource.get("file_url", ""),
                source_domain=resource.get("source_domain"),
                content_snippet=resource.get("content_snippet", "")[:500] if resource.get("content_snippet") else None,
                resource_type=resource_type,
                course_code=course_code,
                course_name=course_name,
                college_id=college_id,
                relevance_score=resource.get("relevance_score", 0.5),
                final_score=resource.get("final_score", 50.0),
                ai_confidence=resource.get("ai_confidence", 0.5),
            )
            
            resources_added += 1
            if resource.get("final_score", 0) >= max(settings.high_confidence_threshold, 90):
                high_confidence += 1
            
            details.append({
                "url": resource.get("file_url"),
                "title": resource.get("title"),
                "type": resource_type_str,
                "score": resource.get("final_score", 0),
                "source": resource.get("source"),
                "search_query": resource.get("search_query"),
                "status": "added"
            })
            
        except Exception as e:
            logger.error(f"Error saving resource: {e}")
            details.append({
                "url": resource.get("file_url", "unknown"),
                "status": "error",
                "message": str(e)
            })
    
    return {
        "resources_found": len(result.get("final_resources", [])),
        "resources_added": resources_added,
        "high_confidence": high_confidence,
        "details": details
    }


@router.post("/discover", response_model=DiscoverResponse)
def discover_resources(
    request: DiscoverRequest,
    db: Session = Depends(get_db),
):
    """
    Discover academic resources for a course.
    
    This triggers the full AI pipeline:
    1. Search Agent - finds relevant URLs via DuckDuckGo
    2. Crawl Agent - extracts content from pages
    3. Extraction Agent - structures the data
    4. Relevance Agent - scores relevance (rule-based)
    5. Classification Agent - detects resource type
    6. College Matching Agent - identifies institution
    7. Deduplication Agent - removes duplicates
    8. Scoring Agent - calculates final score
    
    High-confidence results are added to the review queue.
    """
    logger.info(f"Discovery request: {request.course_code} - {request.course_name}")
    
    try:
        result = process_discovery(
            request.course_code,
            request.course_name,
            request.college_name,
            db
        )
        
        return DiscoverResponse(
            status="success",
            message=f"Discovery complete for {request.course_code}",
            resources_found=result["resources_found"],
            resources_added=result["resources_added"],
            high_confidence=result["high_confidence"],
            details=result["details"]
        )
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return DiscoverResponse(
            status="error",
            message=str(e),
            resources_found=0,
            resources_added=0,
            high_confidence=0,
            details=[]
        )


@router.post("/discover/batch")
def discover_batch(
    requests: List[DiscoverRequest],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Queue multiple courses for discovery (runs in background).
    """
    for req in requests:
        background_tasks.add_task(
            process_discovery,
            req.course_code,
            req.course_name,
            req.college_name,
            db
        )
    
    return {
        "status": "queued",
        "message": f"Queued {len(requests)} courses for discovery",
        "courses": [f"{r.course_code}: {r.course_name}" for r in requests]
    }
