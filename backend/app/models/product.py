from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    one_liner: Mapped[Optional[str]] = mapped_column(Text)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(Text)
    growth_goal: Mapped[Optional[str]] = mapped_column(Text)
    main_problem: Mapped[Optional[str]] = mapped_column(Text)
    solution: Mapped[Optional[str]] = mapped_column(Text)
    competitors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    negative_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")

    company: Mapped["Company"] = relationship(back_populates="products")
    search_strategies: Mapped[list["SearchStrategy"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    search_jobs: Mapped[list["SearchJob"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    social_items: Mapped[list["SocialItem"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    leads: Mapped[list["Lead"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    outreach_messages: Mapped[list["OutreachMessage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    insights: Mapped[list["ProductInsight"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    recommendations: Mapped[list["ProductRecommendation"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
