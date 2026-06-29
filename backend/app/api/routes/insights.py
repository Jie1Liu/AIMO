from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.product_insight import ProductInsight
from app.models.product_recommendation import ProductRecommendation
from app.schemas.insight import ProductAdvisorResponse, ProductInsightRead, ProductRecommendationRead
from app.services.product_advisor_service import ProductAdvisorService

router = APIRouter()


@router.post("/api/products/{product_id}/generate-insights", response_model=ProductAdvisorResponse)
def generate_insights(product_id: UUID, db: Session = Depends(get_db)) -> ProductAdvisorResponse:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    insights, recommendations = ProductAdvisorService().generate(db, product)
    db.commit()
    return ProductAdvisorResponse(insights=insights, recommendations=recommendations)


@router.get("/api/products/{product_id}/insights", response_model=list[ProductInsightRead])
def list_insights(product_id: UUID, db: Session = Depends(get_db)) -> list[ProductInsight]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    return (
        db.query(ProductInsight)
        .filter(ProductInsight.product_id == product_id)
        .order_by(ProductInsight.created_at.desc())
        .all()
    )


@router.get("/api/products/{product_id}/recommendations", response_model=list[ProductRecommendationRead])
def list_recommendations(product_id: UUID, db: Session = Depends(get_db)) -> list[ProductRecommendation]:
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundError("Product not found.")
    return (
        db.query(ProductRecommendation)
        .filter(ProductRecommendation.product_id == product_id)
        .order_by(ProductRecommendation.created_at.desc())
        .all()
    )
