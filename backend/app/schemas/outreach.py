from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OutreachMessageCreate(BaseModel):
    message_type: str = "reply"
    selected_platform_account_id: Optional[UUID] = None
    tone: str = "helpful"


class OutreachMessageUpdate(BaseModel):
    selected_platform_account_id: Optional[UUID] = None
    final_text: Optional[str] = None
    draft_text: Optional[str] = None
    tone: Optional[str] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None


class OutreachMessageRead(BaseModel):
    id: UUID
    product_id: UUID
    lead_id: UUID
    selected_platform_account_id: Optional[UUID]
    platform: str
    recipient_platform_id: Optional[str]
    recipient_name: Optional[str]
    message_type: str
    draft_text: str
    final_text: Optional[str]
    tone: str
    risk_level: str
    policy_notes: dict
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutreachLogRead(BaseModel):
    id: UUID
    outreach_message_id: UUID
    platform_account_id: Optional[UUID]
    platform: str
    send_status: str
    platform_response_id: Optional[str]
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendResponse(BaseModel):
    message: OutreachMessageRead
    log: OutreachLogRead
    action: str
