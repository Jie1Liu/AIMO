from __future__ import annotations
from typing import Optional
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "aimo-backend"}
