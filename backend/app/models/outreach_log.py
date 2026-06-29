from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class OutreachLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "outreach_logs"

    outreach_message_id: Mapped[UUID] = mapped_column(
        ForeignKey("outreach_messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform_account_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("platform_accounts.id", ondelete="SET NULL"))
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    send_status: Mapped[str] = mapped_column(Text, nullable=False)
    platform_response_id: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    outreach_message: Mapped["OutreachMessage"] = relationship(back_populates="logs")
    platform_account: Mapped[Optional["PlatformAccount"]] = relationship(back_populates="outreach_logs")
