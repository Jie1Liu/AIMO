from __future__ import annotations
from typing import Optional
from collections import Counter

from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.models.product import Product
from app.models.product_insight import ProductInsight
from app.models.product_recommendation import ProductRecommendation
from app.models.social_item import SocialItem


class ProductAdvisorService:
    def generate(self, db: Session, product: Product) -> tuple[list[ProductInsight], list[ProductRecommendation]]:
        db.query(ProductInsight).filter(ProductInsight.product_id == product.id).delete()
        db.query(ProductRecommendation).filter(ProductRecommendation.product_id == product.id).delete()

        leads = db.query(Lead).filter(Lead.product_id == product.id).all()
        social_items = db.query(SocialItem).filter(SocialItem.product_id == product.id).all()
        intent_counts = Counter(lead.intent_type for lead in leads)
        evidence = [
            {"lead_id": str(lead.id), "platform": lead.platform, "pain_point": lead.pain_point}
            for lead in leads[:5]
        ]

        top_intent = intent_counts.most_common(1)[0][0] if intent_counts else "market_signal"
        insights = [
            ProductInsight(
                product_id=product.id,
                insight_type="pain_point_cluster",
                title="Top market signal",
                summary=f"{len(leads)} lead opportunities were found from {len(social_items)} public social items. The strongest cluster is {top_intent}.",
                evidence_count=len(evidence),
                confidence=0.82 if leads else 0.5,
                evidence=evidence,
            ),
            ProductInsight(
                product_id=product.id,
                insight_type="competitor_signal",
                title="Competitor and alternative language",
                summary="Several signals mention alternatives, comparisons, or gaps in current workflows.",
                evidence_count=sum(1 for lead in leads if lead.intent_type == "competitor_complaint"),
                confidence=0.74,
                evidence=evidence,
            ),
        ]
        recommendations = [
            ProductRecommendation(
                product_id=product.id,
                recommendation_type="positioning",
                title="Lead with the concrete pain point",
                recommendation=f"Position {product.product_name} around solving '{product.main_problem or product.growth_goal or 'the first growth bottleneck'}' before describing automation.",
                reason="High-intent leads respond better when the first sentence mirrors their stated problem.",
                priority="high",
                evidence=evidence,
            ),
            ProductRecommendation(
                product_id=product.id,
                recommendation_type="content_strategy",
                title="Create comparison and workflow content",
                recommendation="Publish short content around alternatives, review queues, and non-spam outreach workflows.",
                reason="The mock market signals cluster around wanting useful outreach without mass messaging.",
                priority="medium",
                evidence=evidence,
            ),
            ProductRecommendation(
                product_id=product.id,
                recommendation_type="feature_priority",
                title="Prioritize human review and account safety",
                recommendation="Make approval, editing, duplicate protection, and per-account limits visible in the product.",
                reason="This supports the compliance-first promise in the product definition.",
                priority="high",
                evidence=evidence,
            ),
        ]
        db.add_all(insights + recommendations)
        db.flush()
        return insights, recommendations
