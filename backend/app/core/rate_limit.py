from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone

from app.models.platform_account import PlatformAccount


def reset_daily_counter_if_needed(account: PlatformAccount) -> None:
    if account.last_reset_at is None:
        account.last_reset_at = datetime.now(timezone.utc)
        return

    last_reset = account.last_reset_at
    if last_reset.tzinfo is None:
        last_reset = last_reset.replace(tzinfo=timezone.utc)

    if last_reset.date() < datetime.now(timezone.utc).date():
        account.daily_sent_count = 0
        account.last_reset_at = datetime.now(timezone.utc)


def can_send_today(account: PlatformAccount) -> bool:
    reset_daily_counter_if_needed(account)
    return account.daily_sent_count < account.daily_send_limit
