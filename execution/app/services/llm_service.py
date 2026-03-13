from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.schemas.models import DecisionStatus


class LLMService:
    def __init__(self) -> None:
        self.enabled = settings.llm_mode.lower() == "api" and bool(settings.openai_api_key)
        self.client = None
        if self.enabled:
            self.client = OpenAI(base_url=settings.openai_base_url, api_key=settings.openai_api_key)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def _chat(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], int]:
        if not self.client:
            raise RuntimeError("LLM client is not configured")
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        total_tokens = int(getattr(response.usage, "total_tokens", 0) or 0)
        return payload, total_tokens

    def refine_decision(self, decision_payload: dict[str, Any], context_payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if not self.enabled:
            return decision_payload, 0

        system_prompt = (
            "Ты AI-аналитик тендеров. Верни JSON без markdown. "
            "Сохрани поля: status, confidence, confidence_reason, reasons, risks, next_actions. "
            "Статус только GO/REVIEW/NO_GO. Не придумывай факты без evidence."
        )
        user_prompt = json.dumps({"decision": decision_payload, "context": context_payload}, ensure_ascii=False)
        candidate, tokens = self._chat(system_prompt, user_prompt)

        status = str(candidate.get("status", decision_payload.get("status", "REVIEW"))).upper()
        if status not in {DecisionStatus.GO.value, DecisionStatus.REVIEW.value, DecisionStatus.NO_GO.value}:
            status = DecisionStatus.REVIEW.value

        merged = {
            **decision_payload,
            "status": status,
            "confidence": float(candidate.get("confidence", decision_payload.get("confidence", 0.6))),
            "confidence_reason": str(candidate.get("confidence_reason", decision_payload.get("confidence_reason", ""))),
            "reasons": list(candidate.get("reasons", decision_payload.get("reasons", [])))[:5],
            "risks": list(candidate.get("risks", decision_payload.get("risks", [])))[:5],
            "next_actions": list(candidate.get("next_actions", decision_payload.get("next_actions", [])))[:5],
        }
        return merged, tokens

    def enrich_bid_outline(self, outline_payload: dict[str, Any], context_payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if not self.enabled:
            return outline_payload, 0

        system_prompt = (
            "Ты AI-редактор тендерной заявки. Верни JSON без markdown. "
            "Сохрани поля title, required_sections, recommended_sections, missing_information, submission_checklist."
        )
        user_prompt = json.dumps({"outline": outline_payload, "context": context_payload}, ensure_ascii=False)
        candidate, tokens = self._chat(system_prompt, user_prompt)

        merged = {
            **outline_payload,
            "title": str(candidate.get("title", outline_payload.get("title", "Черновик заявки"))),
            "required_sections": list(candidate.get("required_sections", outline_payload.get("required_sections", [])))[:12],
            "recommended_sections": list(candidate.get("recommended_sections", outline_payload.get("recommended_sections", [])))[:12],
            "missing_information": list(candidate.get("missing_information", outline_payload.get("missing_information", [])))[:12],
            "submission_checklist": list(candidate.get("submission_checklist", outline_payload.get("submission_checklist", [])))[:12],
        }
        return merged, tokens
