from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.product_advisor_service import ProductAdvisorService


def process_product_insights(db: Session, product_id: UUID) -> None:
    product = db.get(Product, product_id)
    if product:
        ProductAdvisorService().generate(db, product)
        db.commit()
