"""
Courses API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
def list_courses(
    college_id: Optional[int] = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List courses."""
    courses = crud.get_courses(db, skip, limit, college_id, active_only)
    return courses


@router.post("/", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
):
    """Create a new course."""
    existing = crud.get_course_by_code(db, course.course_code, course.college_id)
    if existing:
        raise HTTPException(status_code=400, detail="Course already exists")
    
    new_course = crud.create_course(
        db, course.course_code, course.course_name, course.college_id
    )
    return new_course


@router.get("/{course_code}")
def get_course(
    course_code: str,
    college_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get course by code."""
    course = crud.get_course_by_code(db, course_code, college_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
