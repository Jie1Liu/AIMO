from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class SearchJob(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "search_jobs"

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    search_strategy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("search_strategies.id", ondelete="SET NULL"),
    )
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    raw_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="search_jobs")
    search_strategy: Mapped[Optional["SearchStrategy"]] = relationship(back_populates="search_jobs")
    social_items: Mapped[list["SocialItem"]] = relationship(back_populates="search_job")
