from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class OutreachMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outreach_messages"

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    selected_platform_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("platform_accounts.id", ondelete="SET NULL"),
    )
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_platform_id: Mapped[Optional[str]] = mapped_column(Text)
    recipient_name: Mapped[Optional[str]] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(Text, nullable=False)
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_text: Mapped[Optional[str]] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(Text, nullable=False, default="helpful")
    risk_level: Mapped[str] = mapped_column(Text, nullable=False, default="medium")
    policy_notes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending_review")

    product: Mapped["Product"] = relationship(back_populates="outreach_messages")
    lead: Mapped["Lead"] = relationship(back_populates="outreach_messages")
    selected_platform_account: Mapped[Optional["PlatformAccount"]] = relationship(back_populates="outreach_messages")
    logs: Mapped[list["OutreachLog"]] = relationship(back_populates="outreach_message", cascade="all, delete-orphan")
