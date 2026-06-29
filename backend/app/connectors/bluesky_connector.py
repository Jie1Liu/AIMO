from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta, timezone
from hashlib import sha1

from app.connectors.base import BaseConnector, SocialItemDTO
from app.models.product import Product


class BlueskyConnector(BaseConnector):
    platform = "bluesky"

    def search(self, product: Product, query_text: str, limit: int = 3) -> list[SocialItemDTO]:
        samples = [
            f"Trying to understand where {product.target_audience or 'founders'} talk about {product.main_problem or 'growth problems'}.",
            f"I need better market signals before rewriting our landing page. {query_text}",
            f"Anyone using AI for product marketing without turning outreach into spam?",
        ]
        return [
            self._item(product, query_text, idx, text)
            for idx, text in enumerate(samples[:limit], start=1)
        ]

    def _item(self, product: Product, query_text: str, idx: int, text: str) -> SocialItemDTO:
        digest = sha1(f"bluesky:{product.id}:{query_text}:{idx}".encode("utf-8")).hexdigest()[:12]
        return SocialItemDTO(
            platform=self.platform,
            platform_item_id=f"bsky_{digest}",
            platform_author_id=f"did:plc:{digest}",
            author_name=f"Bluesky Builder {idx}",
            content_text=text,
            content_url=f"https://bsky.app/profile/example.bsky.social/post/{digest}",
            source_title="Bluesky public post",
            source_context=query_text,
            engagement_score=55 - idx * 5,
            published_at=datetime.now(timezone.utc) - timedelta(hours=idx * 12),
            raw_json={"mock": True, "query": query_text},
        )
