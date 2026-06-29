from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import build_secret_ref
from app.models.company import Company
from app.models.platform_account import PlatformAccount
from app.schemas.platform_account import PlatformAccountCreate, PlatformAccountRead, PlatformAccountUpdate

router = APIRouter()


@router.post("/api/platform-accounts", response_model=PlatformAccountRead)
def create_platform_account(payload: PlatformAccountCreate, db: Session = Depends(get_db)) -> PlatformAccount:
    company = db.get(Company, payload.company_id)
    if not company:
        raise NotFoundError("Company not found.")
    secret_ref = payload.secret_ref or build_secret_ref(str(payload.company_id), payload.platform, payload.account_label)
    account = PlatformAccount(**payload.model_dump(exclude={"secret_ref"}), secret_ref=secret_ref)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/api/platform-accounts", response_model=list[PlatformAccountRead])
def list_platform_accounts(db: Session = Depends(get_db)) -> list[PlatformAccount]:
    return db.query(PlatformAccount).order_by(PlatformAccount.created_at.desc()).all()


@router.get("/api/companies/{company_id}/platform-accounts", response_model=list[PlatformAccountRead])
def list_company_platform_accounts(company_id: UUID, db: Session = Depends(get_db)) -> list[PlatformAccount]:
    company = db.get(Company, company_id)
    if not company:
        raise NotFoundError("Company not found.")
    return (
        db.query(PlatformAccount)
        .filter(PlatformAccount.company_id == company_id)
        .order_by(PlatformAccount.platform.asc(), PlatformAccount.created_at.desc())
        .all()
    )


@router.get("/api/platform-accounts/{account_id}", response_model=PlatformAccountRead)
def get_platform_account(account_id: UUID, db: Session = Depends(get_db)) -> PlatformAccount:
    account = db.get(PlatformAccount, account_id)
    if not account:
        raise NotFoundError("Platform account not found.")
    return account


@router.patch("/api/platform-accounts/{account_id}", response_model=PlatformAccountRead)
def update_platform_account(
    account_id: UUID,
    payload: PlatformAccountUpdate,
    db: Session = Depends(get_db),
) -> PlatformAccount:
    account = db.get(PlatformAccount, account_id)
    if not account:
        raise NotFoundError("Platform account not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account
