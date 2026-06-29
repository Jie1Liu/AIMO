from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outreach_message import OutreachMessage
from app.services.outreach_service import OutreachService


def process_outreach_send(db: Session, outreach_message_id: UUID) -> None:
    message = db.get(OutreachMessage, outreach_message_id)
    if message:
        OutreachService().send(db, message)
        db.commit()
