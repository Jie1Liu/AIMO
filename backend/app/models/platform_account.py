from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PlatformAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_accounts"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    account_label: Mapped[str] = mapped_column(Text, nullable=False)
    platform_user_id: Mapped[Optional[str]] = mapped_column(Text)
    platform_username: Mapped[Optional[str]] = mapped_column(Text)
    auth_type: Mapped[str] = mapped_column(Text, nullable=False)
    secret_ref: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="connected")
    daily_send_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    daily_sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="platform_accounts")
    outreach_messages: Mapped[list["OutreachMessage"]] = relationship(back_populates="selected_platform_account")
    outreach_logs: Mapped[list["OutreachLog"]] = relationship(back_populates="platform_account")
