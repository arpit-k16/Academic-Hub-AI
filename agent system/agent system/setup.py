#!/usr/bin/env python3
"""
Complete Setup Script for Academic Resource Discovery System
This script creates the entire project structure and all source files.
Run: python setup.py
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory structure
DIRECTORIES = [
    "agents",
    "api",
    "api/routes",
    "db",
    "dashboard",
    "workers",
    "config",
    "utils",
    "scripts",
    "tests",
]

# ============================================================================
# FILE CONTENTS - All project source code
# ============================================================================

FILES = {}

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
FILES["config/__init__.py"] = '''"""Config package."""
from .settings import settings, get_settings

__all__ = ["settings", "get_settings"]
'''

FILES["config/settings.py"] = '''"""
Configuration settings for the Academic Resource Discovery System.
Uses pydantic-settings for environment variable management.
"""

from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="Academic Resource Discovery System")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/academic_resources"
    )
    database_async_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/academic_resources"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")
    
    # LLM Provider
    llm_provider: str = Field(default="openai")  # "openai" or "ollama"
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama2")
    
    # SerpAPI
    serpapi_key: Optional[str] = Field(default=None)
    
    # Crawler Settings
    crawler_max_results_per_query: int = Field(default=15)
    crawler_timeout_seconds: int = Field(default=30)
    crawler_delay_between_requests: float = Field(default=1.0)
    
    # Scoring Thresholds
    relevance_threshold: float = Field(default=0.6)
    final_score_threshold: int = Field(default=70)
    high_confidence_threshold: int = Field(default=80)
    
    # Trusted Domains
    trusted_domains: str = Field(
        default=".edu,.ac.in,.gov,uktech.ac.in,uou.ac.in"
    )
    
    # Scheduler
    crawl_interval_hours: int = Field(default=6)
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    # Streamlit
    streamlit_port: int = Field(default=8501)
    
    @property
    def trusted_domains_list(self) -> List[str]:
        """Get trusted domains as a list."""
        return [d.strip() for d in self.trusted_domains.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
'''

# -----------------------------------------------------------------------------
# UTILS
# -----------------------------------------------------------------------------
FILES["utils/__init__.py"] = '''"""Utils package."""
from .llm import get_llm, LLMProvider
from .helpers import (
    extract_domain,
    hash_content,
    hash_url,
    clean_text,
    extract_file_type,
)

__all__ = [
    "get_llm",
    "LLMProvider",
    "extract_domain",
    "hash_content",
    "hash_url",
    "clean_text",
    "extract_file_type",
]
'''

FILES["utils/llm.py"] = '''"""
LLM Provider abstraction - supports OpenAI and Ollama.
"""

from typing import Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.language_models.base import BaseLanguageModel

from config.settings import settings


LLMProvider = Literal["openai", "ollama"]


def get_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
) -> BaseLanguageModel:
    """
    Get LLM instance based on provider configuration.
    
    Args:
        provider: LLM provider ("openai" or "ollama"). Defaults to settings.
        model: Model name. Defaults to settings.
        temperature: Model temperature for responses.
    
    Returns:
        Configured LLM instance.
    """
    provider = provider or settings.llm_provider
    
    if provider == "openai":
        model = model or settings.openai_model
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.openai_api_key,
        )
    elif provider == "ollama":
        model = model or settings.ollama_model
        return Ollama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def get_structured_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
):
    """Get LLM configured for structured output."""
    return get_llm(provider, model, temperature)
'''

FILES["utils/helpers.py"] = '''"""
Utility helper functions.
"""

import re
import hashlib
from urllib.parse import urlparse
from typing import Optional


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content."""
    if not content:
        return ""
    normalized = re.sub(r"\\s+", " ", content.lower().strip())
    return hashlib.sha256(normalized.encode()).hexdigest()


def hash_url(url: str) -> str:
    """Generate SHA-256 hash of URL."""
    if not url:
        return ""
    normalized = url.lower().strip().rstrip("/")
    return hashlib.sha256(normalized.encode()).hexdigest()


def clean_text(text: str, max_length: int = 1000) -> str:
    """Clean and truncate text content."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r"\\s+", " ", text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r"[^\\w\\s.,!?;:\\-()\\[\\]]", "", text)
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text.strip()


def extract_file_type(url: str, content_type: Optional[str] = None) -> str:
    """Extract file type from URL or content type."""
    # Check content type first
    if content_type:
        if "pdf" in content_type.lower():
            return "pdf"
        elif "html" in content_type.lower():
            return "html"
        elif "word" in content_type.lower() or "msword" in content_type.lower():
            return "doc"
        elif "powerpoint" in content_type.lower():
            return "ppt"
    
    # Check URL extension
    url_lower = url.lower()
    if url_lower.endswith(".pdf"):
        return "pdf"
    elif url_lower.endswith(".doc") or url_lower.endswith(".docx"):
        return "doc"
    elif url_lower.endswith(".ppt") or url_lower.endswith(".pptx"):
        return "ppt"
    elif url_lower.endswith(".html") or url_lower.endswith(".htm"):
        return "html"
    else:
        return "html"  # Default to HTML


def is_trusted_domain(domain: str, trusted_list: list) -> bool:
    """Check if domain is in trusted list."""
    domain = domain.lower()
    for trusted in trusted_list:
        if trusted.startswith("."):
            if domain.endswith(trusted):
                return True
        else:
            if domain == trusted or domain.endswith("." + trusted):
                return True
    return False


def calculate_domain_trust(domain: str, trusted_list: list) -> float:
    """Calculate trust score for domain."""
    if is_trusted_domain(domain, trusted_list):
        return 1.5  # Boost for trusted domains
    elif ".edu" in domain or ".ac." in domain:
        return 1.3
    elif ".gov" in domain:
        return 1.2
    elif ".org" in domain:
        return 1.0
    else:
        return 0.8  # Slight penalty for unknown domains
'''

# -----------------------------------------------------------------------------
# DATABASE
# -----------------------------------------------------------------------------
FILES["db/__init__.py"] = '''"""Database package."""
from .database import (
    Base,
    sync_engine,
    async_engine,
    get_sync_db,
    get_async_db,
    get_db,
    init_db,
)
from .models import (
    College,
    Course,
    Resource,
    TrustedDomain,
    CrawlJob,
    ResourceStatus,
    ResourceType,
)

__all__ = [
    "Base",
    "sync_engine",
    "async_engine",
    "get_sync_db",
    "get_async_db",
    "get_db",
    "init_db",
    "College",
    "Course",
    "Resource",
    "TrustedDomain",
    "CrawlJob",
    "ResourceStatus",
    "ResourceType",
]
'''

FILES["db/database.py"] = '''"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager, asynccontextmanager

from config.settings import settings

# Sync engine for Celery workers and scripts
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.database_async_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factories
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


@contextmanager
def get_sync_db():
    """Get synchronous database session (for Celery workers)."""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db():
    """Get async database session (for FastAPI)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db():
    """FastAPI dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=sync_engine)


async def init_db_async():
    """Initialize database tables asynchronously."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
'''

FILES["db/models.py"] = '''"""
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
'''

FILES["db/crud.py"] = '''"""
CRUD operations for database models.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    College, Course, Resource, TrustedDomain, CrawlJob,
    ResourceStatus, ResourceType
)


# ============================================================================
# College CRUD
# ============================================================================

async def get_colleges(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[College]:
    result = await db.execute(select(College).offset(skip).limit(limit))
    return result.scalars().all()


async def get_college_by_id(db: AsyncSession, college_id: int) -> Optional[College]:
    result = await db.execute(select(College).where(College.id == college_id))
    return result.scalar_one_or_none()


async def get_college_by_domain(db: AsyncSession, domain: str) -> Optional[College]:
    result = await db.execute(
        select(College).where(College.domain.ilike(f"%{domain}%"))
    )
    return result.scalar_one_or_none()


async def create_college(db: AsyncSession, name: str, short_name: str = None, domain: str = None) -> College:
    college = College(name=name, short_name=short_name, domain=domain)
    db.add(college)
    await db.flush()
    return college


# ============================================================================
# Course CRUD
# ============================================================================

async def get_courses(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    college_id: Optional[int] = None,
    active_only: bool = True
) -> List[Course]:
    query = select(Course)
    if college_id:
        query = query.where(Course.college_id == college_id)
    if active_only:
        query = query.where(Course.is_active == True)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_course_by_code(
    db: AsyncSession, 
    course_code: str, 
    college_id: Optional[int] = None
) -> Optional[Course]:
    query = select(Course).where(Course.course_code == course_code)
    if college_id:
        query = query.where(Course.college_id == college_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_course(
    db: AsyncSession,
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
    await db.flush()
    return course


def get_all_courses_sync(db: Session) -> List[Course]:
    """Sync version for Celery workers."""
    return db.query(Course).filter(Course.is_active == True).all()


# ============================================================================
# Resource CRUD
# ============================================================================

async def get_resources(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ResourceStatus] = None,
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
    min_score: Optional[float] = None,
) -> List[Resource]:
    query = select(Resource)
    
    filters = []
    if status:
        filters.append(Resource.status == status)
    if course_code:
        filters.append(Resource.course_code == course_code)
    if college_id:
        filters.append(Resource.college_id == college_id)
    if resource_type:
        filters.append(Resource.resource_type == resource_type)
    if min_score is not None:
        filters.append(Resource.final_score >= min_score)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Resource.final_score.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_pending_resources(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
) -> List[Resource]:
    return await get_resources(
        db, skip, limit, 
        status=ResourceStatus.PENDING,
        course_code=course_code,
        college_id=college_id,
        resource_type=resource_type
    )


async def get_resource_by_url(db: AsyncSession, url: str) -> Optional[Resource]:
    result = await db.execute(select(Resource).where(Resource.file_url == url))
    return result.scalar_one_or_none()


async def get_resource_by_url_hash(db: AsyncSession, url_hash: str) -> Optional[Resource]:
    result = await db.execute(select(Resource).where(Resource.url_hash == url_hash))
    return result.scalar_one_or_none()


async def create_resource(db: AsyncSession, **kwargs) -> Resource:
    resource = Resource(**kwargs)
    db.add(resource)
    await db.flush()
    return resource


async def update_resource_status(
    db: AsyncSession,
    resource_id: int,
    status: ResourceStatus,
    reviewed_by: Optional[str] = None,
    rejection_reason: Optional[str] = None
) -> Optional[Resource]:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if resource:
        resource.status = status
        resource.reviewed_by = reviewed_by
        resource.reviewed_at = datetime.utcnow()
        if rejection_reason:
            resource.rejection_reason = rejection_reason
        await db.flush()
    return resource


def check_duplicate_sync(db: Session, url_hash: str, content_hash: str) -> Optional[Resource]:
    """Check for duplicates (sync version for workers)."""
    return db.query(Resource).filter(
        or_(
            Resource.url_hash == url_hash,
            and_(Resource.content_hash == content_hash, Resource.content_hash != "")
        )
    ).first()


def create_resource_sync(db: Session, **kwargs) -> Resource:
    """Create resource (sync version for workers)."""
    resource = Resource(**kwargs)
    db.add(resource)
    db.flush()
    return resource


# ============================================================================
# TrustedDomain CRUD
# ============================================================================

async def get_trusted_domain(db: AsyncSession, domain: str) -> Optional[TrustedDomain]:
    result = await db.execute(
        select(TrustedDomain).where(TrustedDomain.domain == domain)
    )
    return result.scalar_one_or_none()


async def update_domain_stats(
    db: AsyncSession,
    domain: str,
    approved: bool
) -> TrustedDomain:
    result = await db.execute(
        select(TrustedDomain).where(TrustedDomain.domain == domain)
    )
    td = result.scalar_one_or_none()
    
    if not td:
        td = TrustedDomain(domain=domain)
        db.add(td)
    
    if approved:
        td.approved_count += 1
    else:
        td.rejected_count += 1
    
    td.update_trust_score()
    await db.flush()
    return td


def get_domain_trust_score_sync(db: Session, domain: str) -> float:
    """Get trust score for domain (sync)."""
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


async def get_crawl_jobs(db: AsyncSession, limit: int = 10) -> List[CrawlJob]:
    result = await db.execute(
        select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


# ============================================================================
# Statistics
# ============================================================================

async def get_resource_stats(db: AsyncSession) -> dict:
    """Get resource statistics."""
    total = await db.execute(select(func.count(Resource.id)))
    pending = await db.execute(
        select(func.count(Resource.id)).where(Resource.status == ResourceStatus.PENDING)
    )
    approved = await db.execute(
        select(func.count(Resource.id)).where(Resource.status == ResourceStatus.APPROVED)
    )
    rejected = await db.execute(
        select(func.count(Resource.id)).where(Resource.status == ResourceStatus.REJECTED)
    )
    
    return {
        "total": total.scalar() or 0,
        "pending": pending.scalar() or 0,
        "approved": approved.scalar() or 0,
        "rejected": rejected.scalar() or 0,
    }
'''

# -----------------------------------------------------------------------------
# AGENTS
# -----------------------------------------------------------------------------
FILES["agents/__init__.py"] = '''"""Agents package - LangGraph powered AI agents."""
from .workflow import run_discovery_pipeline, ResourceDiscoveryState
from .search_agent import SearchAgent
from .crawl_agent import CrawlAgent
from .extraction_agent import ExtractionAgent
from .relevance_agent import RelevanceAgent
from .classification_agent import ClassificationAgent
from .college_agent import CollegeMatchingAgent
from .dedup_agent import DeduplicationAgent
from .scoring_agent import ScoringAgent

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
'''

FILES["agents/search_agent.py"] = '''"""
Search Agent - Uses SerpAPI to find academic resources.
"""

import time
from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch
from loguru import logger

from config.settings import settings


class SearchAgent:
    """Agent for searching academic resources using SerpAPI."""
    
    QUERY_TEMPLATES = [
        "{course_code} {course_name} notes pdf",
        "{course_code} previous year question paper",
        "{course_name} syllabus pdf",
        "{course_code} study material",
        "{course_name} lecture notes",
        "{course_code} practical manual",
        "{course_name} tutorial pdf",
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.serpapi_key
        if not self.api_key:
            logger.warning("SerpAPI key not configured!")
    
    def generate_queries(self, course_code: str, course_name: str) -> List[str]:
        """Generate search queries for a course."""
        queries = []
        for template in self.QUERY_TEMPLATES:
            query = template.format(
                course_code=course_code,
                course_name=course_name
            )
            queries.append(query)
        return queries
    
    def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Execute search and return results."""
        if not self.api_key:
            logger.error("SerpAPI key not configured")
            return []
        
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google",
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            organic_results = results.get("organic_results", [])
            
            processed = []
            for result in organic_results:
                processed.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0),
                    "source": "google",
                })
            
            logger.info(f"Search '{query[:50]}...' returned {len(processed)} results")
            return processed
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_for_course(
        self,
        course_code: str,
        course_name: str,
        max_results_per_query: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for all resource types for a course."""
        all_results = []
        seen_urls = set()
        
        queries = self.generate_queries(course_code, course_name)
        
        for query in queries:
            results = self.search(query, max_results_per_query)
            
            for result in results:
                url = result.get("link", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["search_query"] = query
                    all_results.append(result)
            
            # Rate limiting
            time.sleep(settings.crawler_delay_between_requests)
        
        logger.info(f"Found {len(all_results)} unique results for {course_code}")
        return all_results
'''

FILES["agents/crawl_agent.py"] = '''"""
Crawl Agent - Extracts content from web pages.
"""

import requests
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger

from config.settings import settings
from utils.helpers import extract_file_type, clean_text


class CrawlAgent:
    """Agent for crawling and extracting web page content."""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    def __init__(self, timeout: int = None):
        self.timeout = timeout or settings.crawler_timeout_seconds
    
    def crawl(self, url: str) -> Dict[str, Any]:
        """Crawl a URL and extract content."""
        result = {
            "url": url,
            "success": False,
            "title": "",
            "content": "",
            "file_type": "",
            "content_type": "",
            "error": None,
        }
        
        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            result["content_type"] = content_type
            result["file_type"] = extract_file_type(url, content_type)
            
            # Handle PDFs differently
            if result["file_type"] == "pdf":
                result["success"] = True
                result["title"] = url.split("/")[-1]
                result["content"] = f"[PDF Document: {result['title']}]"
                return result
            
            # Parse HTML
            soup = BeautifulSoup(response.content, "lxml")
            
            # Extract title
            title_tag = soup.find("title")
            result["title"] = title_tag.get_text().strip() if title_tag else ""
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Extract text content
            text_content = soup.get_text(separator=" ", strip=True)
            result["content"] = clean_text(text_content, max_length=1000)
            result["success"] = True
            
            logger.debug(f"Crawled: {url[:60]}... ({len(result['content'])} chars)")
            
        except requests.Timeout:
            result["error"] = "Timeout"
            logger.warning(f"Timeout crawling: {url}")
        except requests.RequestException as e:
            result["error"] = str(e)
            logger.warning(f"Error crawling {url}: {e}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Unexpected error crawling {url}: {e}")
        
        return result
    
    def crawl_multiple(self, urls: list) -> list:
        """Crawl multiple URLs."""
        results = []
        for url in urls:
            result = self.crawl(url)
            results.append(result)
        return results
'''

FILES["agents/extraction_agent.py"] = '''"""
Extraction Agent - Cleans and structures extracted content.
"""

import re
import json
from typing import Dict, Any, List
from loguru import logger


class ExtractionAgent:
    """Agent for cleaning and structuring extracted content."""
    
    # Keywords to detect resource types
    TYPE_KEYWORDS = {
        "notes": ["notes", "lecture", "chapter", "unit", "summary"],
        "question_paper": ["question paper", "previous year", "exam", "test", "pyq", "sample paper"],
        "syllabus": ["syllabus", "curriculum", "course outline", "course content"],
        "practical": ["practical", "lab", "experiment", "laboratory", "manual"],
        "tutorial": ["tutorial", "assignment", "exercise", "worksheet", "practice"],
    }
    
    def extract(self, crawl_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure content from crawl result."""
        if not crawl_result.get("success"):
            return {
                "valid": False,
                "error": crawl_result.get("error", "Crawl failed"),
            }
        
        title = self._clean_title(crawl_result.get("title", ""))
        content = crawl_result.get("content", "")
        
        # Detect keywords
        keywords = self._detect_keywords(title, content)
        
        return {
            "valid": True,
            "title": title,
            "url": crawl_result.get("url", ""),
            "content_snippet": content[:500] if content else "",
            "full_content": content,
            "file_type": crawl_result.get("file_type", "html"),
            "detected_keywords": keywords,
            "keyword_json": json.dumps(keywords),
        }
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize title."""
        if not title:
            return ""
        # Remove common suffixes
        title = re.sub(r"\\s*[-|]\\s*PDF.*$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\\s*[-|]\\s*Download.*$", "", title, flags=re.IGNORECASE)
        # Clean whitespace
        title = " ".join(title.split())
        return title[:200]
    
    def _detect_keywords(self, title: str, content: str) -> List[str]:
        """Detect relevant keywords from title and content."""
        combined = f"{title} {content}".lower()
        found_keywords = []
        
        for category, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
'''

FILES["agents/relevance_agent.py"] = '''"""
Relevance Agent - LLM-powered relevance scoring.
"""

import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from utils.llm import get_llm


RELEVANCE_PROMPT = """You are an academic resource evaluator. Analyze if the given content is a relevant academic resource for the specified course.

Course Code: {course_code}
Course Name: {course_name}

Resource Title: {title}
Content Snippet: {content_snippet}
URL: {url}

Evaluate this resource and respond with a JSON object:
{{
    "is_relevant": true/false,
    "confidence_score": 0-100,
    "reason": "brief explanation",
    "quality_indicators": ["list", "of", "indicators"]
}}

Consider:
1. Does the content match the course subject?
2. Is this educational material (notes, papers, syllabus)?
3. Is it from a credible source?
4. Is it spam, ads, or irrelevant content?

Respond ONLY with the JSON object, no other text."""


class RelevanceAgent:
    """Agent for evaluating resource relevance using LLM."""
    
    def __init__(self):
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_template(RELEVANCE_PROMPT)
        self.parser = JsonOutputParser()
    
    def evaluate(
        self,
        course_code: str,
        course_name: str,
        title: str,
        content_snippet: str,
        url: str,
    ) -> Dict[str, Any]:
        """Evaluate relevance of a resource."""
        try:
            chain = self.prompt | self.llm | self.parser
            
            result = chain.invoke({
                "course_code": course_code,
                "course_name": course_name,
                "title": title,
                "content_snippet": content_snippet[:500],
                "url": url,
            })
            
            return {
                "is_relevant": result.get("is_relevant", False),
                "confidence_score": result.get("confidence_score", 0),
                "reason": result.get("reason", ""),
                "quality_indicators": result.get("quality_indicators", []),
            }
            
        except Exception as e:
            logger.error(f"Relevance evaluation error: {e}")
            return {
                "is_relevant": False,
                "confidence_score": 0,
                "reason": f"Evaluation error: {str(e)}",
                "quality_indicators": [],
            }
'''

FILES["agents/classification_agent.py"] = '''"""
Classification Agent - Detects resource type.
"""

import json
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from utils.llm import get_llm


CLASSIFICATION_PROMPT = """Classify this academic resource into one of the following types:
- notes: Lecture notes, study notes, chapter summaries
- question_paper: Previous year papers, sample papers, exam papers
- syllabus: Course syllabus, curriculum, course outline
- practical: Lab manuals, practical guides, experiments
- tutorial: Tutorials, assignments, exercises, worksheets
- reference: Reference materials, books, additional reading
- other: If none of the above fit

Resource Title: {title}
Content Snippet: {content_snippet}
Detected Keywords: {keywords}

Respond with JSON:
{{
    "resource_type": "one of the types above",
    "confidence": 0-100,
    "reasoning": "brief explanation"
}}

Respond ONLY with the JSON object."""


class ClassificationAgent:
    """Agent for classifying resource types."""
    
    TYPE_KEYWORD_MAP = {
        "notes": ["notes", "lecture", "chapter", "unit", "summary", "study material"],
        "question_paper": ["question paper", "previous year", "exam", "test paper", "pyq", "solved paper"],
        "syllabus": ["syllabus", "curriculum", "course outline", "course structure"],
        "practical": ["practical", "lab", "experiment", "laboratory", "manual"],
        "tutorial": ["tutorial", "assignment", "exercise", "worksheet", "problem set"],
        "reference": ["reference", "book", "textbook", "reading"],
    }
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        if use_llm:
            self.llm = get_llm()
            self.prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
            self.parser = JsonOutputParser()
    
    def classify(
        self,
        title: str,
        content_snippet: str,
        keywords: list = None,
    ) -> Dict[str, Any]:
        """Classify resource type."""
        # Try keyword-based classification first
        keyword_result = self._classify_by_keywords(title, content_snippet, keywords or [])
        
        if keyword_result["confidence"] >= 80:
            return keyword_result
        
        # Fall back to LLM if enabled
        if self.use_llm:
            return self._classify_with_llm(title, content_snippet, keywords or [])
        
        return keyword_result
    
    def _classify_by_keywords(
        self,
        title: str,
        content: str,
        keywords: list
    ) -> Dict[str, Any]:
        """Classify based on keywords."""
        combined = f"{title} {content} {' '.join(keywords)}".lower()
        
        scores = {}
        for resource_type, type_keywords in self.TYPE_KEYWORD_MAP.items():
            score = sum(1 for kw in type_keywords if kw in combined)
            if score > 0:
                scores[resource_type] = score
        
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = min(100, scores[best_type] * 30)
            return {
                "resource_type": best_type,
                "confidence": confidence,
                "reasoning": f"Keyword match: {scores}",
            }
        
        return {
            "resource_type": "other",
            "confidence": 30,
            "reasoning": "No strong keyword matches",
        }
    
    def _classify_with_llm(
        self,
        title: str,
        content_snippet: str,
        keywords: list,
    ) -> Dict[str, Any]:
        """Classify using LLM."""
        try:
            chain = self.prompt | self.llm | self.parser
            
            result = chain.invoke({
                "title": title,
                "content_snippet": content_snippet[:500],
                "keywords": ", ".join(keywords),
            })
            
            return {
                "resource_type": result.get("resource_type", "other"),
                "confidence": result.get("confidence", 50),
                "reasoning": result.get("reasoning", ""),
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "resource_type": "other",
                "confidence": 0,
                "reasoning": f"Error: {str(e)}",
            }
'''

FILES["agents/college_agent.py"] = '''"""
College Matching Agent - Matches resources to colleges.
"""

import re
from typing import Dict, Any, Optional, List
from loguru import logger


class CollegeMatchingAgent:
    """Agent for matching resources to colleges based on domain and content."""
    
    # Known college domain patterns
    KNOWN_COLLEGES = {
        "uktech.ac.in": {"name": "Uttarakhand Technical University", "short": "UTU"},
        "uou.ac.in": {"name": "Uttarakhand Open University", "short": "UOU"},
        "hnbgu.ac.in": {"name": "Hemwati Nandan Bahuguna Garhwal University", "short": "HNBGU"},
        "du.ac.in": {"name": "Delhi University", "short": "DU"},
        "iitd.ac.in": {"name": "IIT Delhi", "short": "IITD"},
        "iitb.ac.in": {"name": "IIT Bombay", "short": "IITB"},
        "bits-pilani.ac.in": {"name": "BITS Pilani", "short": "BITS"},
    }
    
    def __init__(self, additional_colleges: Dict[str, Dict] = None):
        self.colleges = self.KNOWN_COLLEGES.copy()
        if additional_colleges:
            self.colleges.update(additional_colleges)
    
    def match(
        self,
        url: str,
        content: str = "",
        title: str = "",
    ) -> Dict[str, Any]:
        """Match resource to a college."""
        # Extract domain from URL
        domain = self._extract_domain(url)
        
        # Try domain matching first
        domain_match = self._match_by_domain(domain)
        if domain_match["confidence"] >= 90:
            return domain_match
        
        # Try content matching
        content_match = self._match_by_content(f"{title} {content}")
        if content_match["confidence"] > domain_match["confidence"]:
            return content_match
        
        return domain_match if domain_match["college_name"] else {
            "college_name": None,
            "college_short": None,
            "confidence": 0,
            "match_source": "none",
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _match_by_domain(self, domain: str) -> Dict[str, Any]:
        """Match college by domain."""
        for college_domain, info in self.colleges.items():
            if college_domain in domain:
                return {
                    "college_name": info["name"],
                    "college_short": info["short"],
                    "confidence": 95,
                    "match_source": "domain",
                }
        
        # Check for generic .ac.in or .edu
        if ".ac.in" in domain or ".edu" in domain:
            return {
                "college_name": None,
                "college_short": None,
                "confidence": 30,
                "match_source": "generic_academic",
            }
        
        return {
            "college_name": None,
            "college_short": None,
            "confidence": 0,
            "match_source": "none",
        }
    
    def _match_by_content(self, content: str) -> Dict[str, Any]:
        """Match college by content mentions."""
        content_lower = content.lower()
        
        for domain, info in self.colleges.items():
            # Check for full name
            if info["name"].lower() in content_lower:
                return {
                    "college_name": info["name"],
                    "college_short": info["short"],
                    "confidence": 85,
                    "match_source": "content_fullname",
                }
            # Check for short name
            if info["short"].lower() in content_lower:
                return {
                    "college_name": info["name"],
                    "college_short": info["short"],
                    "confidence": 70,
                    "match_source": "content_shortname",
                }
        
        return {
            "college_name": None,
            "college_short": None,
            "confidence": 0,
            "match_source": "none",
        }
'''

FILES["agents/dedup_agent.py"] = '''"""
Deduplication Agent - Prevents duplicate entries.
"""

import hashlib
from typing import Dict, Any, Optional, Set
from loguru import logger

from utils.helpers import hash_url, hash_content


class DeduplicationAgent:
    """Agent for detecting and preventing duplicate resources."""
    
    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_content_hashes: Set[str] = set()
    
    def check_duplicate(
        self,
        url: str,
        content: str = "",
        check_db: bool = True,
        db_session = None,
    ) -> Dict[str, Any]:
        """Check if resource is a duplicate."""
        url_hash = hash_url(url)
        content_hash = hash_content(content) if content else ""
        
        result = {
            "is_duplicate": False,
            "url_hash": url_hash,
            "content_hash": content_hash,
            "duplicate_type": None,
            "duplicate_of_id": None,
        }
        
        # Check in-memory cache first
        if url_hash in self.seen_urls:
            result["is_duplicate"] = True
            result["duplicate_type"] = "url_memory"
            logger.debug(f"Duplicate URL found in memory: {url[:50]}")
            return result
        
        if content_hash and content_hash in self.seen_content_hashes:
            result["is_duplicate"] = True
            result["duplicate_type"] = "content_memory"
            logger.debug(f"Duplicate content found in memory")
            return result
        
        # Check database if session provided
        if check_db and db_session:
            from db.crud import check_duplicate_sync
            existing = check_duplicate_sync(db_session, url_hash, content_hash)
            if existing:
                result["is_duplicate"] = True
                result["duplicate_type"] = "database"
                result["duplicate_of_id"] = existing.id
                logger.debug(f"Duplicate found in database: {existing.id}")
                return result
        
        # Add to cache
        self.seen_urls.add(url_hash)
        if content_hash:
            self.seen_content_hashes.add(content_hash)
        
        return result
    
    def reset_cache(self):
        """Clear in-memory cache."""
        self.seen_urls.clear()
        self.seen_content_hashes.clear()
'''

FILES["agents/scoring_agent.py"] = '''"""
Scoring Agent - Calculates final scores for resources.
"""

from typing import Dict, Any
from loguru import logger

from config.settings import settings
from utils.helpers import calculate_domain_trust


class ScoringAgent:
    """Agent for calculating final resource scores."""
    
    # Weight configuration
    WEIGHTS = {
        "relevance": 0.40,
        "type_confidence": 0.20,
        "college_confidence": 0.15,
        "domain_trust": 0.25,
    }
    
    def __init__(self, threshold: int = None):
        self.threshold = threshold or settings.final_score_threshold
    
    def score(
        self,
        relevance_score: float,
        type_confidence: float,
        college_confidence: float,
        domain: str,
    ) -> Dict[str, Any]:
        """Calculate final score for a resource."""
        # Normalize scores to 0-100
        relevance_norm = min(100, max(0, relevance_score))
        type_norm = min(100, max(0, type_confidence))
        college_norm = min(100, max(0, college_confidence))
        
        # Calculate domain trust
        domain_trust = calculate_domain_trust(domain, settings.trusted_domains_list)
        domain_score = domain_trust * 66.67  # Scale to ~100
        
        # Calculate weighted score
        final_score = (
            relevance_norm * self.WEIGHTS["relevance"] +
            type_norm * self.WEIGHTS["type_confidence"] +
            college_norm * self.WEIGHTS["college_confidence"] +
            domain_score * self.WEIGHTS["domain_trust"]
        )
        
        # Determine if it passes threshold
        passes_threshold = final_score >= self.threshold
        
        return {
            "final_score": round(final_score, 2),
            "domain_trust_score": round(domain_trust, 2),
            "passes_threshold": passes_threshold,
            "threshold": self.threshold,
            "score_breakdown": {
                "relevance": round(relevance_norm * self.WEIGHTS["relevance"], 2),
                "type_confidence": round(type_norm * self.WEIGHTS["type_confidence"], 2),
                "college_confidence": round(college_norm * self.WEIGHTS["college_confidence"], 2),
                "domain_trust": round(domain_score * self.WEIGHTS["domain_trust"], 2),
            },
        }
'''

FILES["agents/workflow.py"] = '''"""
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
) -> ResourceDiscoveryState:
    """Create initial state for workflow."""
    return ResourceDiscoveryState(
        course_code=course_code,
        course_name=course_name,
        college_id=college_id,
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
        settings.crawler_max_results_per_query,
    )
    
    return {
        "search_results": results,
        "stats": {**state["stats"], "searched": len(results)},
    }


def crawl_node(state: ResourceDiscoveryState) -> Dict[str, Any]:
    """Crawl search results."""
    logger.info(f"Crawling {len(state['search_results'])} URLs")
    
    agent = CrawlAgent()
    results = []
    
    for item in state["search_results"]:
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
    
    for item in state["classified_results"]:
        match = agent.match(
            item.get("url", ""),
            item.get("full_content", ""),
            item.get("title", ""),
        )
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
) -> ResourceDiscoveryState:
    """Run the full discovery pipeline for a course."""
    logger.info(f"Starting pipeline for: {course_code} - {course_name}")
    
    initial_state = create_initial_state(course_code, course_name, college_id)
    workflow = get_workflow()
    
    try:
        final_state = workflow.invoke(initial_state)
        logger.info(f"Pipeline complete. Found {len(final_state['final_resources'])} resources")
        return final_state
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        initial_state["errors"].append(str(e))
        return initial_state
'''

# -----------------------------------------------------------------------------
# API
# -----------------------------------------------------------------------------
FILES["api/__init__.py"] = '''"""API package."""
'''

FILES["api/main.py"] = '''"""
FastAPI main application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from config.settings import settings
from db.database import init_db_async
from api.routes import resources, courses, colleges


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Academic Resource Discovery System")
    await init_db_async()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Agentic AI Academic Resource Discovery System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(colleges.router, prefix="/api/colleges", tags=["Colleges"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
'''

FILES["api/routes/__init__.py"] = '''"""API routes package."""
'''

FILES["api/routes/resources.py"] = '''"""
Resources API routes.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
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
async def list_resources(
    status: Optional[ResourceStatus] = None,
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
    min_score: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List resources with filters."""
    resources = await crud.get_resources(
        db, skip, limit, status, course_code, college_id, resource_type, min_score
    )
    return resources


@router.get("/pending", response_model=List[ResourceResponse])
async def list_pending(
    course_code: Optional[str] = None,
    college_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List pending resources for review."""
    resources = await crud.get_pending_resources(
        db, skip, limit, course_code, college_id, resource_type
    )
    return resources


@router.put("/{resource_id}/review")
async def review_resource(
    resource_id: int,
    update: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a resource."""
    resource = await crud.update_resource_status(
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
    await crud.update_domain_stats(
        db, domain, update.status == ResourceStatus.APPROVED
    )
    
    return {"status": "success", "resource_id": resource_id}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get resource statistics."""
    stats = await crud.get_resource_stats(db)
    return stats
'''

FILES["api/routes/courses.py"] = '''"""
Courses API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from db.database import get_db
from db import crud


router = APIRouter()


class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    college_id: Optional[int] = None


class CourseResponse(BaseModel):
    id: int
    course_code: str
    course_name: str
    college_id: Optional[int]
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    college_id: Optional[int] = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List courses."""
    courses = await crud.get_courses(db, skip, limit, college_id, active_only)
    return courses


@router.post("/", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new course."""
    existing = await crud.get_course_by_code(db, course.course_code, course.college_id)
    if existing:
        raise HTTPException(status_code=400, detail="Course already exists")
    
    new_course = await crud.create_course(
        db, course.course_code, course.course_name, course.college_id
    )
    return new_course


@router.get("/{course_code}")
async def get_course(
    course_code: str,
    college_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get course by code."""
    course = await crud.get_course_by_code(db, course_code, college_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
'''

FILES["api/routes/colleges.py"] = '''"""
Colleges API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from db.database import get_db
from db import crud


router = APIRouter()


class CollegeCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    domain: Optional[str] = None


class CollegeResponse(BaseModel):
    id: int
    name: str
    short_name: Optional[str]
    domain: Optional[str]
    trust_score: float
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CollegeResponse])
async def list_colleges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List all colleges."""
    colleges = await crud.get_colleges(db, skip, limit)
    return colleges


@router.post("/", response_model=CollegeResponse)
async def create_college(
    college: CollegeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new college."""
    new_college = await crud.create_college(
        db, college.name, college.short_name, college.domain
    )
    return new_college


@router.get("/{college_id}", response_model=CollegeResponse)
async def get_college(
    college_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get college by ID."""
    college = await crud.get_college_by_id(db, college_id)
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    return college
'''

# -----------------------------------------------------------------------------
# WORKERS (Celery)
# -----------------------------------------------------------------------------
FILES["workers/__init__.py"] = '''"""Workers package."""
'''

FILES["workers/celery_app.py"] = '''"""
Celery application configuration.
"""

from celery import Celery
from celery.schedules import crontab

from config.settings import settings


celery_app = Celery(
    "academic_resources",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Scheduled tasks (beat)
celery_app.conf.beat_schedule = {
    "crawl-all-courses": {
        "task": "workers.tasks.crawl_all_courses",
        "schedule": crontab(minute=0, hour=f"*/{settings.crawl_interval_hours}"),
    },
}
'''

FILES["workers/tasks.py"] = '''"""
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
            errors="\\n".join(errors) if errors else None,
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
'''

# -----------------------------------------------------------------------------
# DASHBOARD (Streamlit)
# -----------------------------------------------------------------------------
FILES["dashboard/app.py"] = '''"""
Streamlit Review Dashboard.
"""

import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Configuration
API_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Academic Resource Review",
    page_icon="📚",
    layout="wide",
)


def get_pending_resources(filters=None):
    """Fetch pending resources from API."""
    try:
        params = {"status": "pending", "limit": 50}
        if filters:
            params.update(filters)
        response = requests.get(f"{API_URL}/resources/pending", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching resources: {e}")
        return []


def get_stats():
    """Fetch statistics from API."""
    try:
        response = requests.get(f"{API_URL}/resources/stats")
        response.raise_for_status()
        return response.json()
    except:
        return {"total": 0, "pending": 0, "approved": 0, "rejected": 0}


def review_resource(resource_id: int, status: str, reviewer: str = "admin", reason: str = None):
    """Submit review for a resource."""
    try:
        data = {
            "status": status,
            "reviewed_by": reviewer,
        }
        if reason:
            data["rejection_reason"] = reason
        
        response = requests.put(
            f"{API_URL}/resources/{resource_id}/review",
            json=data
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error reviewing resource: {e}")
        return False


def get_courses():
    """Fetch courses for filter."""
    try:
        response = requests.get(f"{API_URL}/courses/", params={"limit": 500})
        response.raise_for_status()
        return response.json()
    except:
        return []


def get_colleges():
    """Fetch colleges for filter."""
    try:
        response = requests.get(f"{API_URL}/colleges/")
        response.raise_for_status()
        return response.json()
    except:
        return []


# Main app
st.title("📚 Academic Resource Review Dashboard")

# Sidebar - Statistics and Filters
with st.sidebar:
    st.header("📊 Statistics")
    stats = get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Total", stats.get("total", 0))
    col2.metric("Pending", stats.get("pending", 0))
    
    col3, col4 = st.columns(2)
    col3.metric("Approved", stats.get("approved", 0))
    col4.metric("Rejected", stats.get("rejected", 0))
    
    st.divider()
    st.header("🔍 Filters")
    
    # Course filter
    courses = get_courses()
    course_options = ["All"] + [c.get("course_code", "") for c in courses]
    selected_course = st.selectbox("Course", course_options)
    
    # College filter
    colleges = get_colleges()
    college_options = ["All"] + [c.get("name", "") for c in colleges]
    selected_college = st.selectbox("College", college_options)
    
    # Type filter
    type_options = ["All", "notes", "question_paper", "syllabus", "practical", "tutorial", "reference", "other"]
    selected_type = st.selectbox("Resource Type", type_options)
    
    # Refresh button
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()


# Build filters
filters = {}
if selected_course != "All":
    filters["course_code"] = selected_course
if selected_college != "All":
    college = next((c for c in colleges if c.get("name") == selected_college), None)
    if college:
        filters["college_id"] = college.get("id")
if selected_type != "All":
    filters["resource_type"] = selected_type


# Main content - Pending Resources
st.header("📋 Pending Resources")

resources = get_pending_resources(filters)

if not resources:
    st.info("No pending resources to review. Great job! 🎉")
else:
    st.write(f"Showing {len(resources)} pending resources")
    
    for i, resource in enumerate(resources):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"📄 {resource.get('title', 'Untitled')[:80]}")
                
                # Metadata row
                meta_cols = st.columns(4)
                meta_cols[0].write(f"**Course:** {resource.get('course_code', 'N/A')}")
                meta_cols[1].write(f"**Type:** {resource.get('resource_type', 'N/A')}")
                meta_cols[2].write(f"**College:** {resource.get('college_name', 'Unknown')}")
                meta_cols[3].write(f"**Score:** {resource.get('final_score', 0):.1f}")
                
                # Content preview
                with st.expander("View Content Snippet"):
                    st.write(resource.get("content_snippet", "No content available"))
                
                # Link
                st.markdown(f"🔗 [Open Resource]({resource.get('file_url', '#')})")
            
            with col2:
                st.write("**AI Confidence:**")
                confidence = resource.get("ai_confidence", 0)
                st.progress(confidence / 100)
                st.write(f"{confidence}%")
                
                # Review buttons
                resource_id = resource.get("id")
                
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{resource_id}", use_container_width=True):
                        if review_resource(resource_id, "approved"):
                            st.success("Approved!")
                            st.rerun()
                
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{resource_id}", use_container_width=True):
                        if review_resource(resource_id, "rejected"):
                            st.warning("Rejected!")
                            st.rerun()
            
            st.divider()


# Footer
st.markdown("---")
st.markdown("*Academic Resource Discovery System - Review Dashboard*")
'''

# -----------------------------------------------------------------------------
# SCRIPTS
# -----------------------------------------------------------------------------
FILES["scripts/init_db.py"] = '''"""
Initialize database and seed data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import sync_engine, Base, get_sync_db
from db.models import College, Course, TrustedDomain
from config.settings import settings


def init_database():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("Tables created successfully!")


def seed_trusted_domains():
    """Seed initial trusted domains."""
    domains = [
        ("uktech.ac.in", 1.5),
        ("uou.ac.in", 1.5),
        ("hnbgu.ac.in", 1.4),
        ("du.ac.in", 1.4),
        ("iitd.ac.in", 1.5),
        ("iitb.ac.in", 1.5),
        ("nptel.ac.in", 1.5),
        ("swayam.gov.in", 1.4),
    ]
    
    print("Seeding trusted domains...")
    with get_sync_db() as db:
        for domain, score in domains:
            existing = db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()
            if not existing:
                td = TrustedDomain(domain=domain, trust_score=score)
                db.add(td)
        db.commit()
    print("Trusted domains seeded!")


def seed_sample_colleges():
    """Seed sample colleges."""
    colleges = [
        ("Uttarakhand Technical University", "UTU", "uktech.ac.in"),
        ("Uttarakhand Open University", "UOU", "uou.ac.in"),
        ("Delhi University", "DU", "du.ac.in"),
    ]
    
    print("Seeding sample colleges...")
    with get_sync_db() as db:
        for name, short, domain in colleges:
            existing = db.query(College).filter(College.name == name).first()
            if not existing:
                college = College(name=name, short_name=short, domain=domain)
                db.add(college)
        db.commit()
    print("Colleges seeded!")


def seed_sample_courses():
    """Seed sample courses."""
    courses = [
        ("BCAT-001", "Introduction to Computer Science", 1),
        ("CAT-014", "Data Structures", 1),
        ("BBT DSC 101", "Biology Fundamentals", 2),
        ("CS-101", "Programming Basics", 1),
        ("MATH-201", "Advanced Mathematics", 1),
    ]
    
    print("Seeding sample courses...")
    with get_sync_db() as db:
        for code, name, college_id in courses:
            existing = db.query(Course).filter(Course.course_code == code).first()
            if not existing:
                course = Course(course_code=code, course_name=name, college_id=college_id)
                db.add(course)
        db.commit()
    print("Courses seeded!")


def main():
    print("=" * 50)
    print("Database Initialization")
    print("=" * 50)
    
    init_database()
    seed_trusted_domains()
    seed_sample_colleges()
    seed_sample_courses()
    
    print("\\n" + "=" * 50)
    print("Database initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
'''

# -----------------------------------------------------------------------------
# DOCKER
# -----------------------------------------------------------------------------
FILES["Dockerfile"] = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

FILES["docker-compose.yml"] = '''version: "3.8"

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: academic_resources
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d academic_resources"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for Celery
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/academic_resources
      - DATABASE_ASYNC_URL=postgresql+asyncpg://user:password@postgres:5432/academic_resources
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./.env:/app/.env:ro

  # Celery Worker
  celery-worker:
    build: .
    command: celery -A workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/academic_resources
      - DATABASE_ASYNC_URL=postgresql+asyncpg://user:password@postgres:5432/academic_resources
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./.env:/app/.env:ro

  # Celery Beat (Scheduler)
  celery-beat:
    build: .
    command: celery -A workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/academic_resources
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - celery-worker
    volumes:
      - ./.env:/app/.env:ro

  # Streamlit Dashboard
  dashboard:
    build: .
    command: streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0
    ports:
      - "8501:8501"
    depends_on:
      - api
    volumes:
      - ./.env:/app/.env:ro

volumes:
  postgres_data:
'''

# -----------------------------------------------------------------------------
# TESTS
# -----------------------------------------------------------------------------
FILES["tests/__init__.py"] = '''"""Tests package."""
'''

FILES["tests/test_agents.py"] = '''"""
Tests for agent components.
"""

import pytest
from agents.extraction_agent import ExtractionAgent
from agents.classification_agent import ClassificationAgent
from agents.college_agent import CollegeMatchingAgent
from agents.dedup_agent import DeduplicationAgent
from agents.scoring_agent import ScoringAgent
from utils.helpers import hash_url, hash_content, extract_domain


class TestExtractionAgent:
    def test_extract_valid_content(self):
        agent = ExtractionAgent()
        crawl_result = {
            "success": True,
            "title": "CS101 Lecture Notes - Download PDF",
            "content": "These are lecture notes for Computer Science 101. Chapter 1 covers basics.",
            "url": "https://example.com/notes.pdf",
            "file_type": "pdf",
        }
        result = agent.extract(crawl_result)
        assert result["valid"] is True
        assert "CS101 Lecture Notes" in result["title"]
        assert "notes" in result["detected_keywords"]
    
    def test_extract_failed_crawl(self):
        agent = ExtractionAgent()
        crawl_result = {"success": False, "error": "Timeout"}
        result = agent.extract(crawl_result)
        assert result["valid"] is False


class TestClassificationAgent:
    def test_classify_notes(self):
        agent = ClassificationAgent(use_llm=False)
        result = agent.classify(
            "Data Structures Lecture Notes",
            "Chapter 1: Introduction to Arrays and Linked Lists",
            ["notes", "lecture"]
        )
        assert result["resource_type"] == "notes"
        assert result["confidence"] > 50
    
    def test_classify_question_paper(self):
        agent = ClassificationAgent(use_llm=False)
        result = agent.classify(
            "CS101 Previous Year Question Paper 2023",
            "Exam paper with solutions",
            ["question paper", "exam"]
        )
        assert result["resource_type"] == "question_paper"


class TestCollegeMatchingAgent:
    def test_match_by_domain(self):
        agent = CollegeMatchingAgent()
        result = agent.match("https://uktech.ac.in/notes/cs101.pdf")
        assert result["college_name"] == "Uttarakhand Technical University"
        assert result["confidence"] >= 90
    
    def test_no_match(self):
        agent = CollegeMatchingAgent()
        result = agent.match("https://randomsite.com/notes.pdf")
        assert result["college_name"] is None


class TestDeduplicationAgent:
    def test_detect_duplicate_url(self):
        agent = DeduplicationAgent()
        # First check
        result1 = agent.check_duplicate("https://example.com/notes.pdf", "content")
        assert result1["is_duplicate"] is False
        # Second check (same URL)
        result2 = agent.check_duplicate("https://example.com/notes.pdf", "different content")
        assert result2["is_duplicate"] is True
    
    def test_reset_cache(self):
        agent = DeduplicationAgent()
        agent.check_duplicate("https://example.com/test.pdf")
        agent.reset_cache()
        result = agent.check_duplicate("https://example.com/test.pdf")
        assert result["is_duplicate"] is False


class TestScoringAgent:
    def test_score_calculation(self):
        agent = ScoringAgent(threshold=70)
        result = agent.score(
            relevance_score=85,
            type_confidence=90,
            college_confidence=80,
            domain="uktech.ac.in"
        )
        assert result["final_score"] > 70
        assert result["passes_threshold"] is True
    
    def test_low_score(self):
        agent = ScoringAgent(threshold=70)
        result = agent.score(
            relevance_score=30,
            type_confidence=40,
            college_confidence=20,
            domain="unknown.com"
        )
        assert result["passes_threshold"] is False


class TestHelpers:
    def test_hash_url(self):
        hash1 = hash_url("https://example.com/test")
        hash2 = hash_url("https://example.com/test/")
        assert hash1 == hash2  # Normalized
    
    def test_extract_domain(self):
        domain = extract_domain("https://www.example.com/path/to/file")
        assert domain == "www.example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

# -----------------------------------------------------------------------------
# README
# -----------------------------------------------------------------------------
FILES["README.md"] = """# 📚 Agentic AI Academic Resource Discovery System

A production-ready autonomous system for discovering academic resources using multi-agent AI pipelines.

## 🌟 Features

- **Autonomous Web Crawling**: Automatically discovers academic resources across the web
- **Multi-Agent Pipeline**: 9 specialized AI agents working together
- **LLM-Powered Validation**: Uses OpenAI or Ollama for intelligent filtering
- **Human-in-the-Loop**: Final review dashboard for quality assurance
- **Scheduled Crawling**: Automated periodic discovery
- **Domain Trust Scoring**: Learns from approvals/rejections

## 🏗️ Architecture

```
[Search Agent] → [Crawl Agent] → [Extraction Agent] → [Relevance Agent]
                                                            ↓
[Database] ← [Filter] ← [Score Agent] ← [Dedup Agent] ← [College Agent] ← [Classification Agent]
     ↓
[Review Dashboard]
```

## 🚀 Quick Start

### 1. Setup Project

```bash
# Run setup script to create directories and files
python setup.py

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env

# Edit .env with your API keys:
# - OPENAI_API_KEY
# - SERPAPI_KEY
# - Database credentials
```

### 3. Start with Docker (Recommended)

```bash
docker-compose up -d
```

### 4. Or Start Manually

```bash
# Terminal 1: Start PostgreSQL and Redis (or use Docker)
docker-compose up postgres redis -d

# Terminal 2: Initialize database
python scripts/init_db.py

# Terminal 3: Start API
uvicorn api.main:app --reload

# Terminal 4: Start Celery worker
celery -A workers.celery_app worker --loglevel=info

# Terminal 5: Start Celery beat (scheduler)
celery -A workers.celery_app beat --loglevel=info

# Terminal 6: Start dashboard
streamlit run dashboard/app.py
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | "openai" or "ollama" | openai |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `SERPAPI_KEY` | SerpAPI key for search | - |
| `FINAL_SCORE_THRESHOLD` | Minimum score for review | 70 |
| `CRAWL_INTERVAL_HOURS` | Auto-crawl frequency | 6 |

## 📊 API Endpoints

- `GET /api/resources/` - List resources
- `GET /api/resources/pending` - Pending for review
- `PUT /api/resources/{id}/review` - Approve/reject
- `GET /api/resources/stats` - Statistics
- `GET /api/courses/` - List courses
- `GET /api/colleges/` - List colleges

## 🤖 Agent Details

1. **Search Agent**: Generates queries, uses SerpAPI
2. **Crawl Agent**: BeautifulSoup scraping
3. **Extraction Agent**: Content cleaning
4. **Relevance Agent**: LLM-powered scoring
5. **Classification Agent**: Resource type detection
6. **College Agent**: Institution matching
7. **Deduplication Agent**: Hash-based dedup
8. **Scoring Agent**: Final score calculation
9. **Review Agent**: Human review preparation

## 📱 Dashboard

Access at `http://localhost:8501`

Features:
- View pending resources
- Approve/Reject with one click
- Filter by course, college, type
- Real-time statistics

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
├── agents/          # LangGraph agents
├── api/             # FastAPI backend
├── db/              # Database models
├── dashboard/       # Streamlit app
├── workers/         # Celery tasks
├── config/          # Settings
├── utils/           # Helpers
├── scripts/         # Init scripts
└── tests/           # Test suite
```

## 🔒 Security Notes

- Never commit `.env` file
- Use strong database passwords
- Configure CORS for production
- Use HTTPS in production

## 📄 License

MIT License
"""

# ============================================================================
# MAIN SETUP FUNCTION
# ============================================================================

def create_directories():
    """Create all project directories."""
    print("Creating project directories...")
    for directory in DIRECTORIES:
        dir_path = os.path.join(BASE_DIR, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✓ Created: {directory}")
    print("Done!")


def create_files():
    """Create all project files."""
    print("\nCreating project files...")
    for file_path, content in FILES.items():
        full_path = os.path.join(BASE_DIR, file_path)
        
        # Ensure directory exists
        dir_path = os.path.dirname(full_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Created: {file_path}")
    print("Done!")


def copy_env_file():
    """Copy .env.example to .env if not exists."""
    env_example = os.path.join(BASE_DIR, ".env.example")
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_example) and not os.path.exists(env_file):
        shutil.copy(env_example, env_file)
        print("\n✓ Created .env from .env.example")
        print("  Please update .env with your API keys!")


def main():
    print("=" * 60)
    print("Academic Resource Discovery System - Complete Setup")
    print("=" * 60)
    print()
    
    create_directories()
    create_files()
    copy_env_file()
    
    print("\n" + "=" * 60)
    print("Setup complete! All files created.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update .env with your API keys (OPENAI_API_KEY, SERPAPI_KEY)")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Start services: docker-compose up -d")
    print("4. Initialize database: python scripts/init_db.py")
    print("5. Access API: http://localhost:8000")
    print("6. Access Dashboard: http://localhost:8501")
    print("\nOr run everything with: docker-compose up")


if __name__ == "__main__":
    main()
