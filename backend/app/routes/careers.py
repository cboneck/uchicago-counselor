"""
Career and placement API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.models.database import get_db, CareerListing

router = APIRouter()


class CareerOut(BaseModel):
    id: int
    title: str
    employer: str | None
    type: str | None
    description: str | None
    url: str | None

    model_config = {"from_attributes": True}


@router.get("/careers", response_model=list[CareerOut])
async def search_careers(
    q: str = Query(default="", description="Search query"),
    type: str = Query(default="", description="Filter by type: job, internship, grad_school"),
    db: DBSession = Depends(get_db),
):
    """Search career listings."""
    query = db.query(CareerListing)

    if type:
        query = query.filter(CareerListing.type == type)
    if q:
        query = query.filter(
            CareerListing.title.ilike(f"%{q}%")
            | CareerListing.description.ilike(f"%{q}%")
        )

    return query.limit(50).all()
