from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SearchJobRead(BaseModel):
    id: UUID
    product_id: UUID
    search_strategy_id: Optional[UUID]
    platform: str
    query_text: str
    status: str
    raw_count: int
    processed_count: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SocialItemRead(BaseModel):
    id: UUID
    product_id: UUID
    search_job_id: Optional[UUID]
    platform: str
    platform_item_id: str
    platform_author_id: Optional[str]
    author_name: Optional[str]
    content_text: str
    content_url: Optional[str]
    source_title: Optional[str]
    source_context: Optional[str]
    engagement_score: int
    published_at: Optional[datetime]
    raw_json: dict
    content_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
