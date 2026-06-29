from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta, timezone
from hashlib import sha1

from app.connectors.base import BaseConnector, SocialItemDTO
from app.models.product import Product


class YouTubeConnector(BaseConnector):
    platform = "youtube"

    def search(self, product: Product, query_text: str, limit: int = 3) -> list[SocialItemDTO]:
        samples = [
            f"This review is useful, but I still need a tool that helps with {product.growth_goal or 'finding customers'}.",
            f"The workflow breaks when I try to reach {product.target_audience or 'early users'} without sounding spammy.",
            f"Would love a comparison for {product.product_name} style tools and {', '.join(product.competitors[:2]) or 'other platforms'}.",
        ]
        return [
            self._item(product, query_text, idx, text)
            for idx, text in enumerate(samples[:limit], start=1)
        ]

    def _item(self, product: Product, query_text: str, idx: int, text: str) -> SocialItemDTO:
        digest = sha1(f"youtube:{product.id}:{query_text}:{idx}".encode("utf-8")).hexdigest()[:12]
        return SocialItemDTO(
            platform=self.platform,
            platform_item_id=f"yt_{digest}",
            platform_author_id=f"youtube_user_{idx}",
            author_name=f"YouTube Commenter {idx}",
            content_text=text,
            content_url=f"https://youtube.com/watch?v={digest}&lc={idx}",
            source_title="YouTube competitor video comments",
            source_context=query_text,
            engagement_score=61 - idx * 7,
            published_at=datetime.now(timezone.utc) - timedelta(days=idx * 2),
            raw_json={"mock": True, "query": query_text},
        )
