from __future__ import annotations
import httpx

from app.models.outreach_message import OutreachMessage
from app.models.platform_account import PlatformAccount
from app.outbound.base_outbound import BaseOutboundConnector, SendResult
from app.services.bluesky_service import BlueskyService


class BlueskyOutboundConnector(BaseOutboundConnector):
    platform = "bluesky"

    def send(self, account: PlatformAccount, message: OutreachMessage) -> SendResult:
        try:
            item = message.lead.social_item
            uri, _ = BlueskyService().send_reply(
                text=message.final_text or message.draft_text,
                target=item.raw_json,
            )
            return SendResult(status="sent", action="public_reply", platform_response_id=uri)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            return SendResult(status="failed", action="public_reply", error_message=str(exc)[:500])
