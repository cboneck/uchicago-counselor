"""
Course search and detail API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.models.database import get_db, Course, Major, MajorRequirement

router = APIRouter()


class CourseOut(BaseModel):
    id: int
    dept: str
    number: str
    title: str
    description: str | None
    prerequisites: str | None
    instructors: str | None
    quarters: str | None
    units: str | None

    model_config = {"from_attributes": True}


class MajorOut(BaseModel):
    id: int
    name: str
    department: str | None
    type: str | None
    description: str | None

    model_config = {"from_attributes": True}


@router.get("/courses", response_model=list[CourseOut])
async def search_courses(
    q: str = Query(default="", description="Search query"),
    dept: str = Query(default="", description="Department filter"),
    db: DBSession = Depends(get_db),
):
    """Search and filter courses."""
    query = db.query(Course)

    if dept:
        query = query.filter(Course.dept == dept.upper())
    if q:
        query = query.filter(
            Course.title.ilike(f"%{q}%")
            | Course.description.ilike(f"%{q}%")
            | Course.number.ilike(f"%{q}%")
        )

    return query.limit(50).all()


@router.get("/courses/{course_id}", response_model=CourseOut)
async def get_course(course_id: int, db: DBSession = Depends(get_db)):
    """Get a specific course by ID."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/majors", response_model=list[MajorOut])
async def list_majors(db: DBSession = Depends(get_db)):
    """List all majors and minors."""
    return db.query(Major).all()


@router.get("/majors/{major_id}", response_model=MajorOut)
async def get_major(major_id: int, db: DBSession = Depends(get_db)):
    """Get a specific major with its requirements."""
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Major not found")
    return major
