from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

from app.models.outreach_message import OutreachMessage
from app.models.platform_account import PlatformAccount


@dataclass(frozen=True)
class SendResult:
    status: str
    action: str
    platform_response_id: Optional[str] = None
    error_message: Optional[str] = None


class BaseOutboundConnector:
    platform: str

    def send(self, account: PlatformAccount, message: OutreachMessage) -> SendResult:
        raise NotImplementedError
