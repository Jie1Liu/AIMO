from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError, PolicyError
from app.core.security import build_secret_ref
from app.models.company import Company
from app.models.platform_account import PlatformAccount
from app.schemas.integration import BlueskyConnectRequest, BlueskyStatusRead
from app.schemas.platform_account import PlatformAccountRead
from app.services.bluesky_service import BlueskyService

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


@router.get("/bluesky/status", response_model=BlueskyStatusRead)
def bluesky_status(db: Session = Depends(get_db)) -> BlueskyStatusRead:
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.platform == "bluesky", PlatformAccount.status == "connected")
        .order_by(PlatformAccount.created_at.desc())
        .first()
    )
    return BlueskyStatusRead(
        configured=settings.bluesky_is_configured,
        connected=bool(account and settings.bluesky_is_configured),
        handle=settings.bluesky_handle or (account.platform_username if account else None),
        account_id=account.id if account else None,
    )


@router.post("/bluesky/connect", response_model=PlatformAccountRead)
def connect_bluesky(payload: BlueskyConnectRequest, db: Session = Depends(get_db)) -> PlatformAccount:
    company = db.get(Company, payload.company_id)
    if not company:
        raise NotFoundError("Company not found.")
    if not settings.bluesky_is_configured:
        raise PolicyError("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD on the backend first.")

    try:
        session = BlueskyService().create_session()
    except Exception as exc:
        raise PolicyError(f"Bluesky authentication failed: {str(exc)[:240]}") from exc

    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.company_id == payload.company_id,
            PlatformAccount.platform == "bluesky",
        )
        .one_or_none()
    )
    if not account:
        account = PlatformAccount(
            company_id=payload.company_id,
            platform="bluesky",
            account_label=f"@{session.handle}",
            platform_user_id=session.did,
            platform_username=session.handle,
            auth_type="app_password_env",
            secret_ref=build_secret_ref(str(payload.company_id), "bluesky", session.handle),
            status="connected",
            daily_send_limit=5,
        )
        db.add(account)
    else:
        account.account_label = f"@{session.handle}"
        account.platform_user_id = session.did
        account.platform_username = session.handle
        account.auth_type = "app_password_env"
        account.status = "connected"
        account.daily_send_limit = 5
    db.commit()
    db.refresh(account)
    return account
