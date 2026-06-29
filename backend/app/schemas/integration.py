from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BlueskyStatusRead(BaseModel):
    platform: str = "bluesky"
    configured: bool
    connected: bool
    handle: Optional[str] = None
    account_id: Optional[UUID] = None


class BlueskyConnectRequest(BaseModel):
    company_id: UUID
