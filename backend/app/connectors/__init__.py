from __future__ import annotations
from typing import Optional
from app.connectors.base import BaseConnector, SocialItemDTO
from app.connectors.bluesky_connector import BlueskyConnector
from app.connectors.reddit_connector import RedditConnector
from app.connectors.youtube_connector import YouTubeConnector


def get_connector(platform: str) -> BaseConnector:
    connectors: dict[str, BaseConnector] = {
        "reddit": RedditConnector(),
        "youtube": YouTubeConnector(),
        "bluesky": BlueskyConnector(),
    }
    return connectors[platform]


__all__ = ["BaseConnector", "SocialItemDTO", "get_connector"]
