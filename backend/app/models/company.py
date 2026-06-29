from __future__ import annotations
from typing import Optional
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    website_url: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(Text)

    users: Mapped[list["User"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    platform_accounts: Mapped[list["PlatformAccount"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
