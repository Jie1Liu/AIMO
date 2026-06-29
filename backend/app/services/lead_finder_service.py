from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lead import Lead
from app.models.product import Product
from app.models.social_item import SocialItem
from app.services.scoring_service import ScoringService


class LeadFinderService:
    pain_terms = {"struggle", "struggling", "problem", "breaks", "need", "hard", "help", "pain"}
    buying_terms = {"looking for", "alternative", "tool", "solve", "using", "comparison"}

    def __init__(self) -> None:
        self.scoring = ScoringService()

    def classify_and_create_lead(self, db: Session, product: Product, item: SocialItem) -> Optional[Lead]:
        existing = db.query(Lead).filter(Lead.social_item_id == item.id).one_or_none()
        if existing:
            return existing

        text = item.content_text.lower()
        negative_hits = [word for word in product.negative_keywords or [] if word.lower() in text]
        if negative_hits:
            return None

        keyword_hits = [word for word in product.keywords or [] if word.lower() in text]
        competitor_hits = [word for word in product.competitors or [] if word.lower() in text]
        relevance = min(1.0, 0.45 + 0.18 * len(keyword_hits) + 0.12 * len(competitor_hits))
        pain_intensity = 0.8 if any(term in text for term in self.pain_terms) else 0.45
        buying_intent = 0.85 if any(term in text for term in self.buying_terms) else 0.35
        target_fit = 0.8 if product.target_audience and any(part.strip().lower() in text for part in product.target_audience.split(",")) else 0.55
        engagement = min(1.0, max(0.0, item.engagement_score / 100))
        recency = self._recency_score(item)

        score = self.scoring.calculate_score(
            product_relevance=relevance,
            pain_intensity=pain_intensity,
            buying_intent=buying_intent,
            target_user_fit=target_fit,
            engagement_score=engagement,
            recency_score=recency,
        )
        if score < settings.lead_min_score:
            return None

        intent_type = self._intent_type(text, competitor_hits)
        lead = Lead(
            product_id=product.id,
            social_item_id=item.id,
            platform=item.platform,
            author_name=item.author_name,
            author_platform_id=item.platform_author_id,
            intent_type=intent_type,
            lead_score=score,
            confidence=min(0.99, max(0.5, score / 100)),
            pain_point=self._pain_point(product, item),
            user_need=f"Needs a practical way to address: {product.main_problem or product.growth_goal or product.product_name}",
            matched_product_value=product.solution or product.one_liner or product.product_description,
            reason=f"Matched {intent_type} signal from public {item.platform} content.",
        )
        db.add(lead)
        db.flush()
        return lead

    def _intent_type(self, text: str, competitor_hits: list[str]) -> str:
        if competitor_hits:
            return "competitor_complaint"
        if "looking for" in text or "alternative" in text:
            return "buying_intent"
        if "?" in text or "how do" in text:
            return "question"
        return "pain_point"

    def _pain_point(self, product: Product, item: SocialItem) -> str:
        if product.main_problem:
            return product.main_problem
        return item.content_text[:180]

    def _recency_score(self, item: SocialItem) -> float:
        if not item.published_at:
            return 0.5
        published_at = item.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - published_at).days
        if age_days <= 7:
            return 1.0
        if age_days <= 30:
            return 0.7
        return 0.3
