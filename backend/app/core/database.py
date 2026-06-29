from __future__ import annotations
from typing import Optional
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine_options: dict[str, object] = {"pool_pre_ping": True}
if settings.uses_sqlite:
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    if settings.uses_sqlite:
        # Import models before create_all so every table is registered on Base.metadata.
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
