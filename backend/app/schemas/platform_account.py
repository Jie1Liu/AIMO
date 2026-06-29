from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlatformAccountCreate(BaseModel):
    company_id: UUID
    platform: str
    account_label: str
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None
    auth_type: str
    secret_ref: Optional[str] = None
    daily_send_limit: int = Field(default=10, ge=0)


class PlatformAccountUpdate(BaseModel):
    account_label: Optional[str] = None
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None
    auth_type: Optional[str] = None
    secret_ref: Optional[str] = None
    status: Optional[str] = None
    daily_send_limit: Optional[int] = Field(default=None, ge=0)
    daily_sent_count: Optional[int] = Field(default=None, ge=0)


class PlatformAccountRead(BaseModel):
    id: UUID
    company_id: UUID
    platform: str
    account_label: str
    platform_user_id: Optional[str]
    platform_username: Optional[str]
    auth_type: str
    secret_ref: str
    status: str
    daily_send_limit: int
    daily_sent_count: int
    last_reset_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
