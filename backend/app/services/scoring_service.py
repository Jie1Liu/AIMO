from __future__ import annotations
from typing import Optional
class ScoringService:
    def calculate_score(
        self,
        *,
        product_relevance: float,
        pain_intensity: float,
        buying_intent: float,
        target_user_fit: float,
        engagement_score: float,
        recency_score: float,
    ) -> int:
        score = (
            product_relevance * 40
            + pain_intensity * 15
            + buying_intent * 20
            + target_user_fit * 15
            + engagement_score * 5
            + recency_score * 5
        )
        return max(0, min(100, round(score)))
