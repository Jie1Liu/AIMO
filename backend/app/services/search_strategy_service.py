from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.search_strategy import SearchStrategy


class SearchStrategyService:
    platforms = ["bluesky"]

    def generate_for_product(self, db: Session, product: Product, replace_existing: bool = True) -> list[SearchStrategy]:
        if replace_existing:
            db.query(SearchStrategy).filter(SearchStrategy.product_id == product.id).delete()

        keywords = product.keywords or []
        primary_keyword = keywords[0] if keywords else product.product_name
        secondary_keyword = keywords[1] if len(keywords) > 1 else primary_keyword
        tertiary_keyword = keywords[2] if len(keywords) > 2 else secondary_keyword

        raw_strategies = [
            (
                "pain_point",
                primary_keyword,
                95,
            ),
            (
                "buying_intent",
                secondary_keyword,
                88,
            ),
            (
                "pain_point",
                tertiary_keyword,
                82,
            ),
            (
                "buying_intent",
                f"looking for {primary_keyword}",
                70,
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
