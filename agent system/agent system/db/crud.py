"""
CRUD operations for database models.
Synchronous version - works with SQLite and PostgreSQL.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from db.models import (
    College, Course, Resource, TrustedDomain, CrawlJob,
    ResourceStatus, ResourceType
)


# ============================================================================
# College CRUD
# ============================================================================

def get_colleges(db: Session, skip: int = 0, limit: int = 100) -> List[College]:
    return db.query(College).offset(skip).limit(limit).all()


def get_college_by_id(db: Session, college_id: int) -> Optional[College]:
    return db.query(College).filter(College.id == college_id).first()


def get_college_by_domain(db: Session, domain: str) -> Optional[College]:
    return db.query(College).filter(College.domain.ilike(f"%{domain}%")).first()


def create_college(db: Session, name: str, short_name: str = None, domain: str = None) -> College:
    college = College(name=name, short_name=short_name, domain=domain)
    db.add(college)
    db.flush()
    return college


# ============================================================================
# Course CRUD
# ============================================================================

def get_courses(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    college_id: Optional[int] = None,
    active_only: bool = True
) -> List[Course]:
    query = db.query(Course)
    if college_id:
        query = query.filter(Course.college_id == college_id)
    if active_only:
        query = query.filter(Course.is_active == True)
    return query.offset(skip).limit(limit).all()


def get_course_by_code(
    db: Session, 
    course_code: str, 
    college_id: Optional[int] = None
) -> Optional[Course]:
    query = db.query(Course).filter(Course.course_code == course_code)
    if college_id:
        query = query.filter(Course.college_id == college_id)
    return query.first()


def create_course(
    db: Session,
    course_code: str,
    course_name: str,
    college_id: Optional[int] = None
) -> Course:
    course = Course(
        course_code=course_code,
        course_name=course_name,
        college_id=college_id
    )
    db.add(course)
    db.flush()
    return course


def get_all_courses_sync(db: Session) -> List[Course]:
    """Get all active courses."""
    return db.query(Course).filter(Course.is_active == True).all()


# ============================================================================
# Resource CRUD
# ============================================================================

def get_resources(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ResourceStatus] = None,
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
    min_score: Optional[float] = None,
) -> List[Resource]:
    query = db.query(Resource)
    
    if status:
        query = query.filter(Resource.status == status)
    if course_code:
        query = query.filter(Resource.course_code == course_code)
    if college_id:
        query = query.filter(Resource.college_id == college_id)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if min_score is not None:
        query = query.filter(Resource.final_score >= min_score)
    
    return query.order_by(Resource.final_score.desc()).offset(skip).limit(limit).all()


def get_pending_resources(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
) -> List[Resource]:
    return get_resources(
        db, skip, limit, 
        status=ResourceStatus.PENDING,
        course_code=course_code,
        college_id=college_id,
        resource_type=resource_type
    )


def get_resource_by_url(db: Session, url: str) -> Optional[Resource]:
    return db.query(Resource).filter(Resource.file_url == url).first()


def get_resource_by_url_hash(db: Session, url_hash: str) -> Optional[Resource]:
    return db.query(Resource).filter(Resource.url_hash == url_hash).first()


def create_resource(db: Session, **kwargs) -> Resource:
    resource = Resource(**kwargs)
    db.add(resource)
    db.flush()
    return resource


def update_resource_status(
    db: Session,
    resource_id: int,
    status: ResourceStatus,
    reviewed_by: Optional[str] = None,
    rejection_reason: Optional[str] = None
) -> Optional[Resource]:
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if resource:
        resource.status = status
        resource.reviewed_by = reviewed_by
        resource.reviewed_at = datetime.utcnow()
        if rejection_reason:
            resource.rejection_reason = rejection_reason
        db.flush()
    return resource


def check_duplicate_sync(db: Session, url_hash: str, content_hash: str) -> Optional[Resource]:
    """Check for duplicates."""
    return db.query(Resource).filter(
        or_(
            Resource.url_hash == url_hash,
            and_(Resource.content_hash == content_hash, Resource.content_hash != "")
        )
    ).first()


def create_resource_sync(db: Session, **kwargs) -> Resource:
    """Create resource."""
    resource = Resource(**kwargs)
    db.add(resource)
    db.flush()
    return resource


# ============================================================================
# TrustedDomain CRUD
# ============================================================================

def get_trusted_domain(db: Session, domain: str) -> Optional[TrustedDomain]:
    return db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()


def update_domain_stats(db: Session, domain: str, approved: bool) -> TrustedDomain:
    td = db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()
    
    if not td:
        td = TrustedDomain(domain=domain)
        db.add(td)
    
    if approved:
        td.approved_count += 1
    else:
        td.rejected_count += 1
    
    td.update_trust_score()
    db.flush()
    return td


def get_domain_trust_score_sync(db: Session, domain: str) -> float:
    """Get trust score for domain."""
    td = db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()
    return td.trust_score if td else 1.0


# ============================================================================
# CrawlJob CRUD
# ============================================================================

def create_crawl_job_sync(db: Session, job_id: str, total_courses: int) -> CrawlJob:
    job = CrawlJob(
        job_id=job_id,
        total_courses=total_courses,
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.flush()
    return job


def update_crawl_job_sync(db: Session, job_id: str, **kwargs) -> Optional[CrawlJob]:
    job = db.query(CrawlJob).filter(CrawlJob.job_id == job_id).first()
    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        db.flush()
    return job


def get_crawl_jobs(db: Session, limit: int = 10) -> List[CrawlJob]:
    return db.query(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(limit).all()


# ============================================================================
# Statistics
# ============================================================================

def get_resource_stats(db: Session) -> dict:
    """Get resource statistics."""
    total = db.query(func.count(Resource.id)).scalar() or 0
    pending = db.query(func.count(Resource.id)).filter(Resource.status == ResourceStatus.PENDING).scalar() or 0
    approved = db.query(func.count(Resource.id)).filter(Resource.status == ResourceStatus.APPROVED).scalar() or 0
    rejected = db.query(func.count(Resource.id)).filter(Resource.status == ResourceStatus.REJECTED).scalar() or 0
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }


def get_or_create_college(db: Session, name: str, domain: str = None) -> College:
    """Get existing college or create new one."""
    # Try to find by name
    college = db.query(College).filter(
        or_(
            College.name.ilike(f"%{name}%"),
            College.short_name.ilike(f"%{name}%") if name else False
        )
    ).first()
    
    if not college and domain:
        # Try to find by domain
        college = db.query(College).filter(College.domain.ilike(f"%{domain}%")).first()
    
    if not college:
        # Create new
        short_name = "".join(word[0].upper() for word in name.split() if word)[:10]
        college = College(name=name, short_name=short_name, domain=domain)
        db.add(college)
        db.flush()
    
    return college
