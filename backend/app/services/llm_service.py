from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Small OpenAI-compatible gateway with a safe no-key fallback."""

    def rank_leads(
        self,
        *,
        product_name: str,
        product_description: str,
        target_audience: Optional[str],
        main_problem: Optional[str],
        solution: Optional[str],
        candidates: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        api_key = settings.effective_llm_api_key
        if not api_key or not candidates:
            return {}

        instructions = (
            "You are a strict product-market-fit analyst ranking public social posts for human-reviewed "
            "outreach. Judge whether the post author is likely in the target audience and currently has "
            "a problem this product can solve. High scores require concrete evidence in the post: an "
            "explicit pain point, active request for help or recommendations, evaluation of alternatives, "
            "or a near-term workflow need. Lower scores for news, link sharing, generic discussion, vendor "
            "promotion, job posts, engagement bait, or a keyword match without user need. Do not reward "
            "popularity or engagement. Score 80-100 only for a strong, actionable match; 60-79 for a "
            "plausible match; 40-59 for weak/ambiguous evidence; 0-39 for a poor match. Give one short, "
            "evidence-based reason in English. Return every lead exactly once as JSON only: "
            '{"rankings":[{"lead_id":"...","fit_score":0,"reason":"..."}]}'
        )
        payload = {
            "product": {
                "name": product_name,
                "description": product_description,
                "target_audience": target_audience,
                "main_problem": main_problem,
                "solution": solution,
            },
            "candidates": candidates[:24],
        }

        try:
            if settings.llm_api_style == "responses":
                text = self._responses_request(instructions, payload, api_key)
            else:
                text = self._chat_completions_request(
                    instructions,
                    payload,
                    api_key,
                    temperature=0.1,
                )
            return self._extract_rankings(text)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("LLM lead ranking kept heuristic scores (%s).", type(exc).__name__)
            return {}

    def generate_outreach(
        self,
        *,
        product_name: str,
        product_description: str,
        target_audience: Optional[str],
        solution: Optional[str],
        author_name: Optional[str],
        original_text: str,
        pain_point: Optional[str],
        tone: str,
    ) -> tuple[Optional[str], str]:
        api_key = settings.effective_llm_api_key
        if not api_key:
            return None, "template"

        instructions = (
            "You write concise, useful social replies for a human to review. "
            "Open with one specific, useful observation tied to the author's actual problem, not a generic "
            "compliment and not a paraphrase of their post. Answer or help first. Mention the product in at "
            "most one sentence and only when it directly addresses the stated need. "
            "Be transparent that it is the reviewer's product, never invent personal experience, "
            "never pressure the author, and never sound like mass outreach. "
            "Use the same language as the original post. Keep the reply under 280 characters. "
            'Return JSON only: {"draft_text":"..."}'
        )
        payload = {
            "product_name": product_name,
            "product_description": product_description,
            "target_audience": target_audience,
            "solution": solution,
            "author_name": author_name,
            "original_post": original_text[:2200],
            "pain_point": pain_point,
            "tone": tone,
        }

        try:
            if settings.llm_api_style == "responses":
                text = self._responses_request(instructions, payload, api_key)
            else:
                text = self._chat_completions_request(instructions, payload, api_key)
            draft = self._extract_draft(text)
            if draft:
                return draft, settings.llm_model
        except (httpx.HTTPError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("LLM generation fell back to the context template (%s).", type(exc).__name__)
        return None, "template"

    def _chat_completions_request(
        self,
        instructions: str,
        payload: dict[str, Any],
        api_key: str,
        *,
        temperature: float = 0.4,
    ) -> str:
        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        body: dict[str, Any] = {
            "model": settings.llm_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        if settings.llm_enable_thinking is not None:
            body["enable_thinking"] = settings.llm_enable_thinking
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(url, headers=headers, json=body)
            if response.status_code == 400:
                body.pop("response_format", None)
                response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
        return str(data["choices"][0]["message"]["content"])

    def _responses_request(self, instructions: str, payload: dict[str, Any], api_key: str) -> str:
        url = f"{settings.llm_base_url.rstrip('/')}/responses"
        body = {
            "model": settings.llm_model,
            "instructions": instructions,
            "input": json.dumps(payload, ensure_ascii=False),
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
        if data.get("output_text"):
            return str(data["output_text"])
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("text"):
                    return str(content["text"])
        raise ValueError("Model response did not contain text.")

    def _extract_draft(self, text: str) -> Optional[str]:
        cleaned = self._clean_json_text(text)
        try:
            value = json.loads(cleaned)
            draft = value.get("draft_text") if isinstance(value, dict) else None
        except json.JSONDecodeError:
            draft = cleaned
        if not isinstance(draft, str):
            return None
        draft = draft.strip()
        return self._fit_bluesky_limit(draft) if draft else None

    def _extract_rankings(self, text: str) -> dict[str, dict[str, Any]]:
        value = json.loads(self._clean_json_text(text))
        rows = value.get("rankings") if isinstance(value, dict) else None
        if not isinstance(rows, list):
            raise ValueError("Model response did not contain rankings.")

        rankings: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            lead_id = row.get("lead_id")
            fit_score = row.get("fit_score")
            reason = row.get("reason")
            if not isinstance(lead_id, str) or not isinstance(reason, str):
                continue
            try:
                normalized_score = max(0, min(100, round(float(fit_score))))
            except (TypeError, ValueError):
                continue
            normalized_reason = " ".join(reason.split()).strip()
            if normalized_reason:
                rankings[lead_id] = {
                    "fit_score": normalized_score,
                    "reason": normalized_reason[:240],
                }
        return rankings

    def _clean_json_text(self, text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        return re.sub(r"\s*```$", "", cleaned)

    def _fit_bluesky_limit(self, value: str, limit: int = 280) -> str:
        if len(value) <= limit:
            return value
        shortened = value[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:")
        return f"{shortened}…"
