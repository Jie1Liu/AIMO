from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.search_job import SearchJob
from app.schemas.search import SearchJobRead

router = APIRouter()


@router.get("/{job_id}", response_model=SearchJobRead)
def get_search_job(job_id: UUID, db: Session = Depends(get_db)) -> SearchJob:
    job = db.get(SearchJob, job_id)
    if not job:
        raise NotFoundError("Search job not found.")
    return job
