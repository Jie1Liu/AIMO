from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID

from sqlalchemy.orm import Session

from app.connectors import get_connector
from app.connectors.base import SocialItemDTO
from app.core.config import settings
from app.models.product import Product
from app.models.search_job import SearchJob
from app.models.search_strategy import SearchStrategy
from app.models.social_item import SocialItem
from app.services.lead_finder_service import LeadFinderService
from app.services.search_strategy_service import SearchStrategyService


class SearchOrchestrator:
    def __init__(self) -> None:
        self.strategy_service = SearchStrategyService()
        self.lead_finder = LeadFinderService()

    def run_for_product(
        self,
        db: Session,
        product: Product,
        *,
        platforms: Optional[list[str]] = None,
        strategy_ids: Optional[list[UUID]] = None,
        process_now: bool = True,
    ) -> list[SearchJob]:
        strategies = self._load_strategies(db, product, strategy_ids)
        platform_filter = set(platforms or ["bluesky"])
        jobs: list[SearchJob] = []

        for strategy in strategies:
            for platform in strategy.platforms:
                if platform not in platform_filter:
                    continue
                job = SearchJob(
                    product_id=product.id,
                    search_strategy_id=strategy.id,
                    platform=platform,
                    query_text=strategy.query_text,
                    status="running" if process_now else "pending",
                    started_at=datetime.now(timezone.utc) if process_now else None,
                )
                db.add(job)
                db.flush()
                jobs.append(job)
                if process_now:
                    self._process_job(db, product, job)

        db.flush()
        return jobs

    def _load_strategies(
        self,
        db: Session,
        product: Product,
        strategy_ids: Optional[list[UUID]],
    ) -> list[SearchStrategy]:
        query = db.query(SearchStrategy).filter(SearchStrategy.product_id == product.id)
        if strategy_ids:
            query = query.filter(SearchStrategy.id.in_(strategy_ids))
        strategies = query.order_by(SearchStrategy.priority.desc()).all()
        if not strategies and not strategy_ids:
            strategies = self.strategy_service.generate_for_product(db, product)
        return strategies

    def _process_job(self, db: Session, product: Product, job: SearchJob) -> None:
        try:
            connector = get_connector(job.platform)
            items = connector.search(product, job.query_text, limit=settings.mock_search_limit)
            job.raw_count = len(items)
            for dto in items:
                item = self._save_social_item(db, product, job, dto)
                self.lead_finder.classify_and_create_lead(db, product, item)
                job.processed_count += 1
            job.status = "completed"
            job.finished_at = datetime.now(timezone.utc)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.now(timezone.utc)

    def _save_social_item(self, db: Session, product: Product, job: SearchJob, dto: SocialItemDTO) -> SocialItem:
        existing = (
            db.query(SocialItem)
            .filter(
                SocialItem.product_id == product.id,
                SocialItem.platform == dto.platform,
                SocialItem.platform_item_id == dto.platform_item_id,
            )
            .one_or_none()
        )
        if existing:
            return existing

        item = SocialItem(
            product_id=product.id,
            search_job_id=job.id,
            platform=dto.platform,
            platform_item_id=dto.platform_item_id,
            platform_author_id=dto.platform_author_id,
            author_name=dto.author_name,
            content_text=dto.content_text,
            content_url=dto.content_url,
            source_title=dto.source_title,
            source_context=dto.source_context,
            engagement_score=dto.engagement_score,
            published_at=dto.published_at,
            raw_json=dto.raw_json,
            content_hash=sha256(dto.content_text.encode("utf-8")).hexdigest(),
        )
        db.add(item)
        db.flush()
        return item
