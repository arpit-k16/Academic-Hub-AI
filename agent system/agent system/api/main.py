"""
FastAPI main application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from config.settings import settings
from db.database import init_db
from api.routes import resources, courses, colleges, crawl


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Academic Resource Discovery System")
    init_db()  # Initialize database on startup
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Agentic AI Academic Resource Discovery System (No API Keys Required)",
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
app.include_router(crawl.router, prefix="/api/crawl", tags=["Crawl"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "database": "SQLite (no Docker needed)",
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
