from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.search_orchestrator import SearchOrchestrator


def process_product_search(db: Session, product_id: UUID) -> None:
    product = db.get(Product, product_id)
    if product:
        SearchOrchestrator().run_for_product(db, product, process_now=True)
        db.commit()
