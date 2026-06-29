from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


@dataclass(frozen=True)
class BlueskySession:
    did: str
    handle: str
    access_jwt: str
    refresh_jwt: str


class BlueskyService:
    user_agent = "AIMO/1.0 (human-reviewed outreach demo)"

    def search_posts(self, query: str, limit: int) -> list[dict[str, Any]]:
        url = f"{settings.bluesky_public_api_url.rstrip('/')}/xrpc/app.bsky.feed.searchPosts"
        with httpx.Client(timeout=20, headers={"User-Agent": self.user_agent}) as client:
            response = client.get(
                url,
                params={"q": query, "limit": max(1, min(limit, 25)), "sort": "latest"},
            )
            response.raise_for_status()
            data = response.json()
        return list(data.get("posts", []))

    def create_session(self) -> BlueskySession:
        if not settings.bluesky_is_configured:
            raise ValueError("Bluesky handle and app password are not configured.")
        url = f"{settings.bluesky_service_url.rstrip('/')}/xrpc/com.atproto.server.createSession"
        with httpx.Client(timeout=20, headers={"User-Agent": self.user_agent}) as client:
            response = client.post(
                url,
                json={
                    "identifier": settings.bluesky_handle,
                    "password": settings.bluesky_app_password,
                },
            )
            response.raise_for_status()
            data = response.json()
        return BlueskySession(
            did=str(data["did"]),
            handle=str(data["handle"]),
            access_jwt=str(data["accessJwt"]),
            refresh_jwt=str(data["refreshJwt"]),
        )

    def send_reply(self, *, text: str, target: dict[str, Any]) -> tuple[str, str]:
        session = self.create_session()
        target_uri = str(target["uri"])
        target_cid = str(target["cid"])
        root_uri = str(target.get("root_uri") or target_uri)
        root_cid = str(target.get("root_cid") or target_cid)
        url = f"{settings.bluesky_service_url.rstrip('/')}/xrpc/com.atproto.repo.createRecord"
        record = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": self._now_iso(),
            "reply": {
                "root": {"uri": root_uri, "cid": root_cid},
                "parent": {"uri": target_uri, "cid": target_cid},
            },
        }
        with httpx.Client(
            timeout=20,
            headers={
                "Authorization": f"Bearer {session.access_jwt}",
                "User-Agent": self.user_agent,
            },
        ) as client:
            response = client.post(
                url,
                json={
                    "repo": session.did,
                    "collection": "app.bsky.feed.post",
                    "record": record,
                },
            )
            response.raise_for_status()
            data = response.json()
        return str(data["uri"]), str(data["cid"])

    def _now_iso(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
