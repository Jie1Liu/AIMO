from __future__ import annotations
from datetime import datetime
import re

from app.connectors.base import BaseConnector, SocialItemDTO
from app.models.product import Product
from app.services.bluesky_service import BlueskyService


class BlueskyConnector(BaseConnector):
    platform = "bluesky"
    stop_words = {
        "about",
        "after",
        "around",
        "before",
        "building",
        "conversations",
        "early-stage",
        "find",
        "founders",
        "from",
        "help",
        "join",
        "looking",
        "need",
        "product",
        "relevant",
        "right",
        "small",
        "struggle",
        "teams",
        "that",
        "their",
        "this",
        "users",
        "with",
    }

    def search(self, product: Product, query_text: str, limit: int = 3) -> list[SocialItemDTO]:
        search_limit = min(100, max(25, limit * 4))
        posts = BlueskyService().search_posts(self._clean_query(query_text), search_limit)
        items: list[SocialItemDTO] = []
        for post in posts:
            text = str((post.get("record") or {}).get("text") or "")
            if self._is_usable(text) and self._is_relevant(product, text):
                items.append(self._item(query_text, post))
                if len(items) >= limit:
                    break
        return items

    def _clean_query(self, value: str) -> str:
        return value.replace('"', "").replace(" OR ", " ").strip()[:240]

    def _is_usable(self, text: str) -> bool:
        lower = text.lower()
        promotional_terms = {
            "buy now",
            "limited offer",
            "themeforest",
            "download here",
            "coupon code",
        }
        return bool(text.strip()) and text.count("#") <= 4 and not any(
            term in lower for term in promotional_terms
        )

    def _is_relevant(self, product: Product, text: str) -> bool:
        normalized = self._normalize(text)
        keyword_phrases = [
            self._normalize(keyword)
            for keyword in product.keywords or []
            if len(self._normalize(keyword)) >= 4
        ]
        if any(phrase in normalized for phrase in keyword_phrases):
            return True

        signal_source = " ".join(
            [
                *(product.keywords or []),
                product.target_audience or "",
                product.main_problem or "",
            ]
        )
        signal_tokens = {
            self._stem(token)
            for token in re.findall(r"[a-z0-9]+", self._normalize(signal_source))
            if len(token) >= 4 and token not in self.stop_words
        }
        text_tokens = {
            self._stem(token)
            for token in re.findall(r"[a-z0-9]+", normalized)
            if len(token) >= 4
        }
        return len(signal_tokens & text_tokens) >= 2

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().replace("-", " ").split())

    def _stem(self, value: str) -> str:
        if value.endswith("ies") and len(value) > 5:
            return f"{value[:-3]}y"
        if value.endswith("s") and len(value) > 4:
            return value[:-1]
        return value

    def _item(self, query_text: str, post: dict) -> SocialItemDTO:
        author = post.get("author") or {}
        record = post.get("record") or {}
        uri = str(post.get("uri") or "")
        handle = str(author.get("handle") or "")
        rkey = uri.rsplit("/", 1)[-1]
        reply_ref = record.get("reply") or {}
        root_ref = reply_ref.get("root") or {}
        published_at = record.get("createdAt") or post.get("indexedAt")
        published = None
        if published_at:
            iso_value = str(published_at).replace("Z", "+00:00")
            iso_value = re.sub(r"(\.\d{6})\d+([+-]\d{2}:\d{2})$", r"\1\2", iso_value)
            published = datetime.fromisoformat(iso_value)
        return SocialItemDTO(
            platform=self.platform,
            platform_item_id=uri,
            platform_author_id=author.get("did"),
            author_name=handle or author.get("displayName"),
            content_text=str(record.get("text") or ""),
            content_url=f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else None,
            source_title=author.get("displayName") or handle or "Bluesky post",
            source_context=query_text,
            engagement_score=min(
                100,
                int(post.get("likeCount") or 0)
                + int(post.get("replyCount") or 0) * 2
                + int(post.get("repostCount") or 0),
            ),
            published_at=published,
            raw_json={
                "mock": False,
                "query": query_text,
                "uri": uri,
                "cid": post.get("cid"),
                "root_uri": root_ref.get("uri") or uri,
                "root_cid": root_ref.get("cid") or post.get("cid"),
                "author_handle": handle,
                "author_display_name": author.get("displayName"),
                "avatar_url": author.get("avatar"),
            },
        )
