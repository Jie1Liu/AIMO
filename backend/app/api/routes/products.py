from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.search_job import SearchJob
from app.models.search_strategy import SearchStrategy
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    RunSearchRequest,
    SearchStrategyRead,
)
from app.schemas.search import SearchJobRead
from app.services.lead_ranking_service import LeadRankingService
from app.services.product_profile_service import ProductProfileService
from app.services.search_orchestrator import SearchOrchestrator
from app.services.search_strategy_service import SearchStrategyService

router = APIRouter()


@router.post("", response_model=ProductRead)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    product = ProductProfileService().create_product(db, payload)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
def list_products(
    company_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Product]:
    query = db.query(Product)
    if company_id:
        query = query.filter(Product.company_id == company_id)
    return query.order_by(Product.created_at.desc()).all()


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: UUID, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    return product


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: UUID, payload: ProductUpdate, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    ProductProfileService().update_product(product, payload)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: UUID, db: Session = Depends(get_db)) -> Response:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    db.delete(product)
    db.commit()
    return Response(status_code=204)


@router.post("/{product_id}/generate-search-strategies", response_model=list[SearchStrategyRead])
def generate_search_strategies(product_id: UUID, db: Session = Depends(get_db)) -> list[SearchStrategy]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    strategies = SearchStrategyService().generate_for_product(db, product)
    db.commit()
    return strategies


@router.get("/{product_id}/search-strategies", response_model=list[SearchStrategyRead])
def list_search_strategies(product_id: UUID, db: Session = Depends(get_db)) -> list[SearchStrategy]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    return (
        db.query(SearchStrategy)
        .filter(SearchStrategy.product_id == product_id)
        .order_by(SearchStrategy.priority.desc())
        .all()
    )


@router.post("/{product_id}/run-search", response_model=list[SearchJobRead])
def run_search(
    product_id: UUID,
    payload: Optional[RunSearchRequest] = None,
    db: Session = Depends(get_db),
) -> list[SearchJob]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    payload = payload or RunSearchRequest()
    jobs = SearchOrchestrator().run_for_product(
        db,
        product,
        platforms=payload.platforms,
        strategy_ids=payload.strategy_ids,
        process_now=payload.process_now,
    )
    if payload.process_now:
        LeadRankingService().rerank_product(db, product)
    db.commit()
    return jobs


@router.get("/{product_id}/search-jobs", response_model=list[SearchJobRead])
def list_product_search_jobs(product_id: UUID, db: Session = Depends(get_db)) -> list[SearchJob]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    return (
        db.query(SearchJob)
        .filter(SearchJob.product_id == product_id)
        .order_by(SearchJob.created_at.desc())
        .all()
    )
