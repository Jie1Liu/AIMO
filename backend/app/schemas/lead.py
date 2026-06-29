from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.search import SocialItemRead


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    lead_score: Optional[int] = Field(default=None, ge=0, le=100)
    pain_point: Optional[str] = None
    user_need: Optional[str] = None
    matched_product_value: Optional[str] = None
    reason: Optional[str] = None


class LeadRead(BaseModel):
    id: UUID
    product_id: UUID
    social_item_id: UUID
    platform: str
    author_name: Optional[str]
    author_platform_id: Optional[str]
    intent_type: str
    lead_score: int
    confidence: float
    pain_point: Optional[str]
    user_need: Optional[str]
    matched_product_value: Optional[str]
    reason: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    social_item: Optional[SocialItemRead] = None

    model_config = ConfigDict(from_attributes=True)
