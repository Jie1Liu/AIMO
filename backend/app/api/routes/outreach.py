from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.outreach_message import OutreachMessage
from app.models.product import Product
from app.schemas.outreach import OutreachMessageRead, OutreachMessageUpdate, SendResponse
from app.services.outreach_service import OutreachService

router = APIRouter()


@router.get("/api/products/{product_id}/outreach-messages", response_model=list[OutreachMessageRead])
def list_product_outreach_messages(product_id: UUID, db: Session = Depends(get_db)) -> list[OutreachMessage]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    return (
        db.query(OutreachMessage)
        .filter(OutreachMessage.product_id == product_id)
        .order_by(OutreachMessage.created_at.desc())
        .all()
    )


@router.get("/api/outreach-messages/{message_id}", response_model=OutreachMessageRead)
def get_outreach_message(message_id: UUID, db: Session = Depends(get_db)) -> OutreachMessage:
    message = db.get(OutreachMessage, message_id)
    if not message:
        raise NotFoundError("Outreach message not found.")
    return message


@router.patch("/api/outreach-messages/{message_id}", response_model=OutreachMessageRead)
def update_outreach_message(
    message_id: UUID,
    payload: OutreachMessageUpdate,
    db: Session = Depends(get_db),
) -> OutreachMessage:
    message = db.get(OutreachMessage, message_id)
    if not message:
        raise NotFoundError("Outreach message not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(message, field, value)
    db.commit()
    db.refresh(message)
    return message


@router.post("/api/outreach-messages/{message_id}/approve", response_model=OutreachMessageRead)
def approve_outreach_message(message_id: UUID, db: Session = Depends(get_db)) -> OutreachMessage:
    message = db.get(OutreachMessage, message_id)
    if not message:
        raise NotFoundError("Outreach message not found.")
    OutreachService().approve(message)
    db.commit()
    db.refresh(message)
    return message


@router.post("/api/outreach-messages/{message_id}/regenerate", response_model=OutreachMessageRead)
def regenerate_outreach_message(message_id: UUID, db: Session = Depends(get_db)) -> OutreachMessage:
    message = db.get(OutreachMessage, message_id)
    if not message:
        raise NotFoundError("Outreach message not found.")
    OutreachService().regenerate(db, message)
    db.commit()
    db.refresh(message)
    return message


@router.post("/api/outreach-messages/{message_id}/reject", response_model=OutreachMessageRead)
def reject_outreach_message(message_id: UUID, db: Session = Depends(get_db)) -> OutreachMessage:
    message = db.get(OutreachMessage, message_id)
    if not message:
        raise NotFoundError("Outreach message not found.")
    OutreachService().reject(message)
    db.commit()
    db.refresh(message)
    return message


@router.post("/api/outreach-messages/{message_id}/send", response_model=SendResponse)
def send_outreach_message(message_id: UUID, db: Session = Depends(get_db)) -> SendResponse:
    message = db.get(OutreachMessage, message_id)
    if not message:
        raise NotFoundError("Outreach message not found.")
    message, log, action = OutreachService().send(db, message)
    db.commit()
    db.refresh(message)
    db.refresh(log)
    return SendResponse(message=message, log=log, action=action)
