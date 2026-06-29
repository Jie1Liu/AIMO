from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProductInsightRead(BaseModel):
    id: UUID
    product_id: UUID
    insight_type: str
    title: str
    summary: str
    evidence_count: int
    confidence: float
    evidence: list[dict]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductRecommendationRead(BaseModel):
    id: UUID
    product_id: UUID
    recommendation_type: str
    title: str
    recommendation: str
    reason: Optional[str]
    priority: str
    evidence: list[dict]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductAdvisorResponse(BaseModel):
    insights: list[ProductInsightRead]
    recommendations: list[ProductRecommendationRead]
