from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.models.product import Product


@dataclass(frozen=True)
class SocialItemDTO:
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
    raw_json: dict = field(default_factory=dict)


class BaseConnector:
    platform: str

    def search(self, product: Product, query_text: str, limit: int = 3) -> list[SocialItemDTO]:
        raise NotImplementedError
