from __future__ import annotations
from typing import Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class VectorType(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dimensions})"


class SocialItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "social_items"
    __table_args__ = (UniqueConstraint("platform", "platform_item_id", "product_id"),)

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    search_job_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("search_jobs.id", ondelete="SET NULL"))
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    platform_item_id: Mapped[str] = mapped_column(Text, nullable=False)
    platform_author_id: Mapped[Optional[str]] = mapped_column(Text)
    author_name: Mapped[Optional[str]] = mapped_column(Text)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(Text)
    source_title: Mapped[Optional[str]] = mapped_column(Text)
    source_context: Mapped[Optional[str]] = mapped_column(Text)
    engagement_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    raw_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(VectorType(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="social_items")
    search_job: Mapped[Optional["SearchJob"]] = relationship(back_populates="social_items")
    lead: Mapped[Optional["Lead"]] = relationship(back_populates="social_item")
