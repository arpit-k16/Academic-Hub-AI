"""
Resources API routes.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db
from db import crud
from db.models import ResourceStatus, ResourceType


router = APIRouter()


class ResourceResponse(BaseModel):
    id: int
    title: str
    file_url: str
    source_domain: Optional[str]
    content_snippet: Optional[str]
    resource_type: str
    course_code: Optional[str]
    course_name: Optional[str]
    college_name: Optional[str]
    relevance_score: float
    final_score: float
    ai_confidence: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResourceUpdate(BaseModel):
    status: ResourceStatus
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class StatsResponse(BaseModel):
    total: int
    pending: int
    approved: int
    rejected: int


@router.get("/", response_model=List[ResourceResponse])
def list_resources(
    status: Optional[ResourceStatus] = None,
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
    min_score: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List resources with filters."""
    resources = crud.get_resources(
        db, skip, limit, status, course_code, college_id, resource_type, min_score
    )
    return resources


@router.get("/pending", response_model=List[ResourceResponse])
def list_pending(
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List pending resources for review."""
    resources = crud.get_pending_resources(
        db, skip, limit, course_code, college_id, resource_type
    )
    return resources


@router.put("/{resource_id}/review")
def review_resource(
    resource_id: int,
    update: ResourceUpdate,
    db: Session = Depends(get_db),
):
    """Approve or reject a resource."""
    resource = crud.update_resource_status(
        db,
        resource_id,
        update.status,
        update.reviewed_by,
        update.rejection_reason,
    )
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Update domain trust scores
    from utils.helpers import extract_domain
    domain = extract_domain(resource.file_url)
    crud.update_domain_stats(
        db, domain, update.status == ResourceStatus.APPROVED
    )
    
    return {"status": "success", "resource_id": resource_id}


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Get resource statistics."""
    stats = crud.get_resource_stats(db)
    return stats
