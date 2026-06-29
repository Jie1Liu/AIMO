from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.lead import Lead
from app.models.product import Product
from app.schemas.lead import LeadRead, LeadUpdate
from app.schemas.outreach import OutreachMessageCreate, OutreachMessageRead
from app.services.outreach_service import OutreachService

router = APIRouter()


@router.get("/api/products/{product_id}/leads", response_model=list[LeadRead])
def list_product_leads(
    product_id: UUID,
    platform: Optional[str] = Query(default=None),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    intent_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Lead]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    query = db.query(Lead).options(joinedload(Lead.social_item)).filter(Lead.product_id == product_id)
    if platform:
        query = query.filter(Lead.platform == platform)
    if min_score is not None:
        query = query.filter(Lead.lead_score >= min_score)
    if intent_type:
        query = query.filter(Lead.intent_type == intent_type)
    return query.order_by(Lead.lead_score.desc(), Lead.created_at.desc()).all()


@router.get("/api/leads/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: UUID, db: Session = Depends(get_db)) -> Lead:
    lead = db.query(Lead).options(joinedload(Lead.social_item)).filter(Lead.id == lead_id).one_or_none()
    if not lead:
        raise NotFoundError("Lead not found.")
    return lead


@router.patch("/api/leads/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: UUID, payload: LeadUpdate, db: Session = Depends(get_db)) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise NotFoundError("Lead not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/api/leads/{lead_id}/outreach-message", response_model=OutreachMessageRead)
def create_outreach_message(
    lead_id: UUID,
    payload: Optional[OutreachMessageCreate] = None,
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise NotFoundError("Lead not found.")
    message = OutreachService().create_message(db, lead, payload or OutreachMessageCreate())
    db.commit()
    db.refresh(message)
    return message
