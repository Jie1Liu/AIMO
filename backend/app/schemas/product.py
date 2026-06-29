from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    product_name: str
    one_liner: Optional[str] = None
    product_description: str
    target_audience: Optional[str] = None
    growth_goal: Optional[str] = None
    main_problem: Optional[str] = None
    solution: Optional[str] = None
    competitors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    status: str = "active"


class ProductCreate(ProductBase):
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    one_liner: Optional[str] = None
    product_description: Optional[str] = None
    target_audience: Optional[str] = None
    growth_goal: Optional[str] = None
    main_problem: Optional[str] = None
    solution: Optional[str] = None
    competitors: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    negative_keywords: Optional[list[str]] = None
    status: Optional[str] = None


class ProductRead(ProductBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchStrategyRead(BaseModel):
    id: UUID
    product_id: UUID
    strategy_type: str
    query_text: str
    platforms: list[str]
    priority: int

    model_config = ConfigDict(from_attributes=True)


class RunSearchRequest(BaseModel):
    platforms: Optional[list[str]] = None
    strategy_ids: Optional[list[UUID]] = None
    process_now: bool = True


class ProductWorkflowResponse(BaseModel):
    product: ProductRead
    search_strategies: list[SearchStrategyRead] = Field(default_factory=list)
