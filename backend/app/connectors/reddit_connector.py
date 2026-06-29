from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta, timezone
from hashlib import sha1

from app.connectors.base import BaseConnector, SocialItemDTO
from app.models.product import Product


class RedditConnector(BaseConnector):
    platform = "reddit"

    def search(self, product: Product, query_text: str, limit: int = 3) -> list[SocialItemDTO]:
        base = product.main_problem or product.product_description
        samples = [
            f"I am struggling with {base}. Has anyone found a practical way to solve this?",
            f"Looking for alternatives to {', '.join(product.competitors[:2]) or 'the usual tools'} for {product.target_audience or 'my team'}.",
            f"How do early teams validate positioning before spending weeks on campaigns? {query_text}",
        ]
        return [
            self._item(product, query_text, idx, text)
            for idx, text in enumerate(samples[:limit], start=1)
        ]

    def _item(self, product: Product, query_text: str, idx: int, text: str) -> SocialItemDTO:
        digest = sha1(f"reddit:{product.id}:{query_text}:{idx}".encode("utf-8")).hexdigest()[:12]
        return SocialItemDTO(
            platform=self.platform,
            platform_item_id=f"rd_{digest}",
            platform_author_id=f"reddit_user_{idx}",
            author_name=f"Reddit Founder {idx}",
            content_text=text,
            content_url=f"https://reddit.com/r/startups/comments/{digest}",
            source_title="r/startups discussion",
            source_context=query_text,
            engagement_score=72 - idx * 8,
            published_at=datetime.now(timezone.utc) - timedelta(days=idx),
            raw_json={"mock": True, "query": query_text},
        )
