from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "leads"

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    social_item_id: Mapped[UUID] = mapped_column(ForeignKey("social_items.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[Optional[str]] = mapped_column(Text)
    author_platform_id: Mapped[Optional[str]] = mapped_column(Text)
    intent_type: Mapped[str] = mapped_column(Text, nullable=False)
    lead_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    pain_point: Mapped[Optional[str]] = mapped_column(Text)
    user_need: Mapped[Optional[str]] = mapped_column(Text)
    matched_product_value: Mapped[Optional[str]] = mapped_column(Text)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="new")

    product: Mapped["Product"] = relationship(back_populates="leads")
    social_item: Mapped["SocialItem"] = relationship(back_populates="lead")
    outreach_messages: Mapped[list["OutreachMessage"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
