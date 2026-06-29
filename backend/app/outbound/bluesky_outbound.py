from __future__ import annotations
from typing import Optional
from hashlib import sha1

from app.models.outreach_message import OutreachMessage
from app.models.platform_account import PlatformAccount
from app.outbound.base_outbound import BaseOutboundConnector, SendResult


class BlueskyOutboundConnector(BaseOutboundConnector):
    platform = "bluesky"

    def send(self, account: PlatformAccount, message: OutreachMessage) -> SendResult:
        digest = sha1(f"bluesky:{account.id}:{message.id}".encode("utf-8")).hexdigest()[:12]
        action = "direct_message" if message.message_type == "dm" else "public_reply"
        return SendResult(status="sent", action=action, platform_response_id=f"bsky_{digest}")
