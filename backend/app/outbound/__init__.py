from __future__ import annotations
from typing import Optional
from app.outbound.base_outbound import BaseOutboundConnector, SendResult
from app.outbound.bluesky_outbound import BlueskyOutboundConnector
from app.outbound.reddit_outbound import RedditOutboundConnector
from app.outbound.youtube_outbound import YouTubeOutboundConnector


def get_outbound_connector(platform: str) -> BaseOutboundConnector:
    connectors: dict[str, BaseOutboundConnector] = {
        "reddit": RedditOutboundConnector(),
        "youtube": YouTubeOutboundConnector(),
        "bluesky": BlueskyOutboundConnector(),
    }
    return connectors[platform]


__all__ = ["BaseOutboundConnector", "SendResult", "get_outbound_connector"]
