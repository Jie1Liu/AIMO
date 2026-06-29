from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter()


@router.post("", response_model=CompanyRead)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)) -> list[Company]:
    return db.query(Company).order_by(Company.created_at.desc()).all()


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: UUID, db: Session = Depends(get_db)) -> Company:
    company = db.get(Company, company_id)
    if not company:
        raise NotFoundError("Company not found.")
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: UUID, payload: CompanyUpdate, db: Session = Depends(get_db)) -> Company:
    company = db.get(Company, company_id)
    if not company:
        raise NotFoundError("Company not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
