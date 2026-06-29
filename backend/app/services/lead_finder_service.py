from __future__ import annotations
import re
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lead import Lead
from app.models.product import Product
from app.models.social_item import SocialItem
from app.services.scoring_service import ScoringService


class LeadFinderService:
    pain_terms = {
        "can't",
        "cannot",
        "difficult",
        "frustrated",
        "hard",
        "help",
        "need",
        "pain",
        "problem",
        "stuck",
        "struggle",
        "struggling",
        "wish",
    }
    buying_terms = {
        "alternative",
        "any tool",
        "how can",
        "how do",
        "looking for",
        "need a",
        "recommend",
        "seeking",
        "suggestions",
        "what do you use",
    }
    stop_words = {
        "and",
        "about",
        "after",
        "are",
        "around",
        "before",
        "building",
        "conversations",
        "find",
        "for",
        "from",
        "has",
        "have",
        "help",
        "into",
        "join",
        "looking",
        "need",
        "new",
        "our",
        "product",
        "relevant",
        "right",
        "small",
        "struggle",
        "that",
        "the",
        "their",
        "this",
        "was",
        "were",
        "with",
        "you",
        "your",
    }

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
        signal_tokens = self._tokens(
            " ".join([*(product.keywords or []), product.main_problem or ""])
        )
        audience_tokens = self._tokens(product.target_audience or "")
        text_tokens = self._tokens(text, remove_stop_words=False)
        signal_hits = sorted(signal_tokens & text_tokens)
        audience_hits = sorted(audience_tokens & text_tokens)
        pain_hits = sorted(term for term in self.pain_terms if term in text)
        buying_hits = sorted(term for term in self.buying_terms if term in text)
        has_question = "?" in text or "how " in text
        first_person = bool(re.search(r"\b(i|i'm|im|my|we|we're|our)\b", text))

        relevance = min(
            1.0,
            0.50
            + 0.22 * len(keyword_hits)
            + 0.07 * min(4, len(signal_hits))
            + 0.08 * len(competitor_hits),
        )
        pain_intensity = 0.88 if pain_hits else 0.58 if has_question or first_person else 0.38
        buying_intent = 0.92 if buying_hits else 0.68 if has_question and first_person else 0.42
        target_fit = min(1.0, 0.52 + 0.10 * min(4, len(audience_hits)))
        engagement = min(1.0, max(0.0, item.engagement_score / 20))
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
        reason = self._reason(
            item.platform,
            keyword_hits=keyword_hits,
            signal_hits=signal_hits,
            audience_hits=audience_hits,
            pain_hits=pain_hits,
            buying_hits=buying_hits,
            has_question=has_question,
        )
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
            reason=reason,
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

    def _tokens(self, value: str, *, remove_stop_words: bool = True) -> set[str]:
        tokens = {
            self._stem(token)
            for token in re.findall(r"[a-z0-9]+", value.lower().replace("-", " "))
            if len(token) >= 3
        }
        if remove_stop_words:
            return {token for token in tokens if token not in self.stop_words}
        return tokens

    def _stem(self, value: str) -> str:
        if value.endswith("ies") and len(value) > 5:
            return f"{value[:-3]}y"
        if value.endswith("s") and len(value) > 4:
            return value[:-1]
        return value

    def _reason(
        self,
        platform: str,
        *,
        keyword_hits: list[str],
        signal_hits: list[str],
        audience_hits: list[str],
        pain_hits: list[str],
        buying_hits: list[str],
        has_question: bool,
    ) -> str:
        phrase_tokens = self._tokens(" ".join(keyword_hits), remove_stop_words=False)
        token_evidence = [
            token
            for token in [*signal_hits, *audience_hits]
            if token not in phrase_tokens and token not in self.stop_words
        ]
        matched = list(dict.fromkeys([*keyword_hits, *token_evidence]))[:4]
        evidence: list[str] = []
        if matched:
            evidence.append(f"matched {', '.join(matched)}")
        if buying_hits:
            evidence.append("shows active solution intent")
        elif pain_hits:
            evidence.append("describes a relevant pain point")
        elif has_question:
            evidence.append("asks for practical guidance")
        evidence_text = " and ".join(evidence) or "matches the product context"
        return f"Public {platform} post {evidence_text}."

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
