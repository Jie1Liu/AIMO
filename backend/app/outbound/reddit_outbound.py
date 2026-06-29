from __future__ import annotations
from typing import Optional
from app.models.outreach_message import OutreachMessage
from app.models.platform_account import PlatformAccount
from app.outbound.base_outbound import BaseOutboundConnector, SendResult


class RedditOutboundConnector(BaseOutboundConnector):
    platform = "reddit"

    def send(self, account: PlatformAccount, message: OutreachMessage) -> SendResult:
        return SendResult(
            status="manual_action_required",
            action="copy_or_open_original",
            error_message="Reddit MVP does not auto-send. User must copy the approved message manually.",
        )
