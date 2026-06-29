from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.social_item import SocialItem
from app.services.lead_finder_service import LeadFinderService


def process_social_item(db: Session, social_item_id: UUID) -> None:
    item = db.query(SocialItem).options(joinedload(SocialItem.product)).filter(SocialItem.id == social_item_id).one_or_none()
    if item:
        LeadFinderService().classify_and_create_lead(db, item.product, item)
        db.commit()
