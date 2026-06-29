from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.search_strategy import SearchStrategy


class SearchStrategyService:
    platforms = ["reddit", "youtube", "bluesky"]

    def generate_for_product(self, db: Session, product: Product, replace_existing: bool = True) -> list[SearchStrategy]:
        if replace_existing:
            db.query(SearchStrategy).filter(SearchStrategy.product_id == product.id).delete()

        keywords = product.keywords or []
        competitors = product.competitors or []
        base_problem = product.main_problem or product.product_description
        audience = product.target_audience or "target customers"

        raw_strategies = [
            (
                "pain_point",
                f'"{base_problem}" help OR advice',
                95,
            ),
            (
                "buying_intent",
                f'"looking for" "{keywords[0] if keywords else product.product_name}"',
                88,
            ),
            (
                "competitor_complaint",
                f'"{competitors[0] if competitors else product.product_name}" alternative complaint',
                82,
            ),
            (
                "content_research",
                f'"{audience}" growth marketing questions',
                70,
            ),
            (
                "market_trend",
                f'"{product.product_name}" positioning trend',
                60,
            ),
        ]

        strategies = [
            SearchStrategy(
                product_id=product.id,
                strategy_type=strategy_type,
                query_text=query_text,
                platforms=self.platforms,
                priority=priority,
            )
            for strategy_type, query_text, priority in raw_strategies
        ]
        db.add_all(strategies)
        db.flush()
        return strategies
