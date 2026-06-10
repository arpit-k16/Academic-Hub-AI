"""
Colleges API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
def list_colleges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all colleges."""
    colleges = crud.get_colleges(db, skip, limit)
    return colleges


@router.post("/", response_model=CollegeResponse)
def create_college(
    college: CollegeCreate,
    db: Session = Depends(get_db),
):
    """Create a new college."""
    new_college = crud.create_college(
        db, college.name, college.short_name, college.domain
    )
    return new_college


@router.get("/{college_id}", response_model=CollegeResponse)
def get_college(
    college_id: int,
    db: Session = Depends(get_db),
):
    """Get college by ID."""
    college = crud.get_college_by_id(db, college_id)
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    return college
