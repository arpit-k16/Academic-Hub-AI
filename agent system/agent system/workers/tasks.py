"""
Celery tasks for background processing.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from loguru import logger

from workers.celery_app import celery_app
from db.database import get_sync_db
from db.crud import (
    get_all_courses_sync,
    create_resource_sync,
    check_duplicate_sync,
    create_crawl_job_sync,
    update_crawl_job_sync,
)
from db.models import ResourceStatus
from agents.workflow import run_discovery_pipeline


@celery_app.task(bind=True, max_retries=3)
def process_course(self, course_code: str, course_name: str, college_id: Optional[int] = None):
    """Process a single course through the pipeline."""
    logger.info(f"Processing course: {course_code}")
    
    try:
        # Run the discovery pipeline
        result = run_discovery_pipeline(course_code, course_name, college_id)
        
        # Store results in database
        with get_sync_db() as db:
            added = 0
            duplicates = 0
            
            for resource in result.get("final_resources", []):
                # Check for duplicates
                existing = check_duplicate_sync(
                    db,
                    resource.get("url_hash", ""),
                    resource.get("content_hash", ""),
                )
                
                if existing:
                    duplicates += 1
                    continue
                
                # Create new resource
                create_resource_sync(
                    db,
                    title=resource.get("title", ""),
                    file_url=resource.get("file_url", ""),
                    source_domain=resource.get("source_domain", ""),
                    content_snippet=resource.get("content_snippet", ""),
                    resource_type=resource.get("resource_type", "other"),
                    file_type=resource.get("file_type", "html"),
                    course_code=resource.get("course_code", ""),
                    course_name=resource.get("course_name", ""),
                    college_name=resource.get("college_name"),
                    relevance_score=resource.get("relevance_score", 0),
                    type_confidence=resource.get("type_confidence", 0),
                    college_confidence=resource.get("college_confidence", 0),
                    domain_trust_score=resource.get("domain_trust_score", 1.0),
                    final_score=resource.get("final_score", 0),
                    ai_confidence=resource.get("ai_confidence", 0),
                    relevance_reason=resource.get("relevance_reason", ""),
                    url_hash=resource.get("url_hash", ""),
                    content_hash=resource.get("content_hash", ""),
                    detected_keywords=resource.get("detected_keywords", "[]"),
                    status=ResourceStatus.PENDING,
                    crawled_at=datetime.utcnow(),
                )
                added += 1
            
            db.commit()
        
        return {
            "course_code": course_code,
            "status": "success",
            "resources_found": len(result.get("final_resources", [])),
            "resources_added": added,
            "duplicates_skipped": duplicates,
            "stats": result.get("stats", {}),
        }
        
    except Exception as e:
        logger.error(f"Error processing {course_code}: {e}")
        self.retry(exc=e, countdown=60)


@celery_app.task
def crawl_all_courses():
    """Crawl all active courses."""
    job_id = str(uuid.uuid4())
    logger.info(f"Starting crawl job: {job_id}")
    
    with get_sync_db() as db:
        courses = get_all_courses_sync(db)
        total_courses = len(courses)
        
        # Create job record
        create_crawl_job_sync(db, job_id, total_courses)
        db.commit()
    
    total_added = 0
    total_duplicates = 0
    errors = []
    
    for i, course in enumerate(courses):
        try:
            result = process_course.delay(
                course.course_code,
                course.course_name,
                course.college_id,
            )
            # Wait for result (with timeout)
            task_result = result.get(timeout=600)
            total_added += task_result.get("resources_added", 0)
            total_duplicates += task_result.get("duplicates_skipped", 0)
            
        except Exception as e:
            logger.error(f"Error with course {course.course_code}: {e}")
            errors.append(f"{course.course_code}: {str(e)}")
        
        # Update progress
        with get_sync_db() as db:
            update_crawl_job_sync(
                db, job_id,
                processed_courses=i + 1,
                resources_added=total_added,
                duplicates_skipped=total_duplicates,
            )
            db.commit()
    
    # Mark complete
    with get_sync_db() as db:
        update_crawl_job_sync(
            db, job_id,
            status="completed",
            completed_at=datetime.utcnow(),
            errors="\n".join(errors) if errors else None,
        )
        db.commit()
    
    logger.info(f"Crawl job {job_id} complete. Added: {total_added}, Duplicates: {total_duplicates}")
    return {
        "job_id": job_id,
        "total_courses": total_courses,
        "resources_added": total_added,
        "duplicates_skipped": total_duplicates,
        "errors": len(errors),
    }


@celery_app.task
def trigger_single_crawl(course_code: str, course_name: str, college_id: Optional[int] = None):
    """Trigger crawl for a single course (manual trigger)."""
    return process_course.delay(course_code, course_name, college_id).get(timeout=600)
