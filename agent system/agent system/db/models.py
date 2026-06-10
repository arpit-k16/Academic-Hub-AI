"""
SQLAlchemy models for the Academic Resource Discovery System.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import Base


class ResourceStatus(str, Enum):
    """Status of a resource in the review pipeline."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ResourceType(str, Enum):
    """Type of academic resource."""
    NOTES = "notes"
    QUESTION_PAPER = "question_paper"
    SYLLABUS = "syllabus"
    PRACTICAL = "practical"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    OTHER = "other"


class College(Base):
    """College/University model."""
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    short_name = Column(String(50), nullable=True)
    domain = Column(String(255), nullable=True)
    trust_score = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    courses = relationship("Course", back_populates="college")
    resources = relationship("Resource", back_populates="college")
    
    def __repr__(self):
        return f"<College(id={self.id}, name='{self.name}')>"


class Course(Base):
    """Course model."""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(50), nullable=False, index=True)
    course_name = Column(String(255), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True)
    semester = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    college = relationship("College", back_populates="courses")
    resources = relationship("Resource", back_populates="course")
    
    __table_args__ = (
        UniqueConstraint('course_code', 'college_id', name='uq_course_college'),
        Index('ix_course_code_name', 'course_code', 'course_name'),
    )
    
    def __repr__(self):
        return f"<Course(id={self.id}, code='{self.course_code}')>"


class Resource(Base):
    """Academic resource model."""
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    file_url = Column(String(2048), nullable=False, unique=True)
    source_domain = Column(String(255), nullable=True)
    content_snippet = Column(Text, nullable=True)
    
    resource_type = Column(
        SQLEnum(ResourceType), 
        default=ResourceType.OTHER,
        nullable=False
    )
    
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    course = relationship("Course", back_populates="resources")
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True)
    college = relationship("College", back_populates="resources")
    
    course_code = Column(String(50), nullable=True, index=True)
    course_name = Column(String(255), nullable=True)
    college_name = Column(String(255), nullable=True)
    
    relevance_score = Column(Float, default=0.0)
    type_confidence = Column(Float, default=0.0)
    college_confidence = Column(Float, default=0.0)
    domain_trust_score = Column(Float, default=1.0)
    final_score = Column(Float, default=0.0, index=True)
    ai_confidence = Column(Float, default=0.0)
    relevance_reason = Column(Text, nullable=True)
    
    content_hash = Column(String(64), nullable=True, index=True)
    url_hash = Column(String(64), nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    
    status = Column(
        SQLEnum(ResourceStatus),
        default=ResourceStatus.PENDING,
        nullable=False,
        index=True
    )
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    detected_keywords = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    crawled_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('ix_resource_status_score', 'status', 'final_score'),
        Index('ix_resource_course_type', 'course_code', 'resource_type'),
    )


class TrustedDomain(Base):
    """Trusted domains with dynamic scoring."""
    __tablename__ = "trusted_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    trust_score = Column(Float, default=1.0)
    approved_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def update_trust_score(self):
        """Update trust score based on approval/rejection ratio."""
        total = self.approved_count + self.rejected_count
        if total > 0:
            approval_rate = self.approved_count / total
            self.trust_score = 0.5 + (approval_rate * 0.5)


class CrawlJob(Base):
    """Track crawl jobs."""
    __tablename__ = "crawl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True)
    status = Column(String(50), default="pending")
    total_courses = Column(Integer, default=0)
    processed_courses = Column(Integer, default=0)
    total_resources_found = Column(Integer, default=0)
    resources_added = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
