from __future__ import annotations
from typing import Optional
from hashlib import sha1

from app.models.outreach_message import OutreachMessage
from app.models.platform_account import PlatformAccount
from app.outbound.base_outbound import BaseOutboundConnector, SendResult


class YouTubeOutboundConnector(BaseOutboundConnector):
    platform = "youtube"

    def send(self, account: PlatformAccount, message: OutreachMessage) -> SendResult:
        digest = sha1(f"youtube:{account.id}:{message.id}".encode("utf-8")).hexdigest()[:12]
        return SendResult(status="sent", action="public_comment_reply", platform_response_id=f"yt_reply_{digest}")
