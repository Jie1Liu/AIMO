from __future__ import annotations
from typing import Optional
from hashlib import sha256
from hmac import compare_digest

from app.core.config import settings


def hash_secret(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def verify_secret(value: str, hashed: str) -> bool:
    return compare_digest(hash_secret(value), hashed)


def build_secret_ref(company_id: str, platform: str, account_label: str) -> str:
    safe_label = account_label.lower().replace(" ", "-")
    return f"{settings.secrets_manager_prefix}{company_id}/{platform}/{safe_label}"
