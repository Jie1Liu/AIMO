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
            "Respond to the author's actual problem first. Mention the product only when relevant, "
            "be transparent that it is the reviewer's product, never invent personal experience, "
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

    def _chat_completions_request(self, instructions: str, payload: dict[str, Any], api_key: str) -> str:
        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        body: dict[str, Any] = {
            "model": settings.llm_model,
            "temperature": 0.4,
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
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            value = json.loads(cleaned)
            draft = value.get("draft_text") if isinstance(value, dict) else None
        except json.JSONDecodeError:
            draft = cleaned
        if not isinstance(draft, str):
            return None
        draft = draft.strip()
        return self._fit_bluesky_limit(draft) if draft else None

    def _fit_bluesky_limit(self, value: str, limit: int = 280) -> str:
        if len(value) <= limit:
            return value
        shortened = value[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:")
        return f"{shortened}…"
