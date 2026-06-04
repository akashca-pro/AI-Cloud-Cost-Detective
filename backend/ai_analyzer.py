"""OpenAI enrichment for deterministic FinOps findings (WP2)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from models.responses import AIEnrichment, AnalyzeResponse, EnrichedFinding

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"


class _LLMEnrichmentPayload(BaseModel):
    """Expected JSON shape from the model."""

    summary: str = ""
    estimated_savings: str = ""
    enriched_findings: list[EnrichedFinding] = Field(default_factory=list)


class AIAnalyzer:
    """Enrich rule-based analyze results with narrative summary and AWS CLI fixes."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")

    def enrich(self, response: AnalyzeResponse) -> AIEnrichment:
        if not self._api_key:
            return AIEnrichment(
                skipped=True,
                skip_reason="OPENAI_API_KEY is not configured.",
                summary="AI enrichment skipped.",
            )

        if not response.findings and response.resource_count == 0:
            return AIEnrichment(
                summary="No AWS resources were discovered for the selected filters.",
                estimated_savings="No savings estimated — nothing to optimize.",
                enriched_findings=[],
            )

        if not response.findings:
            return AIEnrichment(
                summary=(
                    f"Scanned {response.resource_count} resource(s) across "
                    f"{', '.join(response.regions_scanned)}. "
                    "No FinOps issues were detected by the rule engine."
                ),
                estimated_savings="No immediate savings identified from rule-based checks.",
                enriched_findings=[],
            )

        try:
            return self._call_openai(response)
        except Exception as exc:
            logger.exception("OpenAI enrichment failed")
            return AIEnrichment(
                skipped=True,
                skip_reason=f"OpenAI enrichment failed: {exc}",
                summary="AI enrichment could not be completed.",
            )

    def _call_openai(self, response: AnalyzeResponse) -> AIEnrichment:
        client = OpenAI(api_key=self._api_key)
        user_content = _build_user_payload(response)

        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        raw = completion.choices[0].message.content or "{}"
        data = json.loads(raw)
        payload = _LLMEnrichmentPayload.model_validate(data)
        return _merge_enrichment(response, payload)


def _build_user_payload(response: AnalyzeResponse) -> str:
    findings_payload = [
        {
            "finding_id": f.finding_id,
            "severity": f.severity,
            "category": f.category,
            "title": f.title,
            "description": f.description,
            "resource_id": f.resource_id,
            "resource_type": f.resource_type,
            "region": f.region,
            "recommendation_hint": f.recommendation_hint,
            "evidence": f.evidence,
        }
        for f in response.findings
    ]
    resources_summary = [
        {
            "resource_id": r.resource_id,
            "resource_type": r.resource_type,
            "region": r.region,
            "name": r.name,
            "tags": r.tags,
        }
        for r in response.resources[:50]
    ]
    body: dict[str, Any] = {
        "account_id": response.account_id,
        "regions_scanned": response.regions_scanned,
        "services_scanned": response.services_scanned,
        "resource_count": response.resource_count,
        "findings_summary": response.findings_summary,
        "findings": findings_payload,
        "resources_sample": resources_summary,
    }
    return json.dumps(body, indent=2)


def _merge_enrichment(
    response: AnalyzeResponse,
    payload: _LLMEnrichmentPayload,
) -> AIEnrichment:
    known_ids = {f.finding_id for f in response.findings}
    enriched: list[EnrichedFinding] = []
    for item in payload.enriched_findings:
        if item.finding_id not in known_ids:
            continue
        enriched.append(item)

    for finding in response.findings:
        if not any(e.finding_id == finding.finding_id for e in enriched):
            enriched.append(
                EnrichedFinding(
                    finding_id=finding.finding_id,
                    ai_explanation=finding.recommendation_hint,
                    fix_command=None,
                )
            )

    return AIEnrichment(
        summary=payload.summary,
        estimated_savings=payload.estimated_savings,
        enriched_findings=enriched,
    )


_SYSTEM_PROMPT = """You are an AWS FinOps assistant. You ENRICH existing rule-based findings; do not invent new infrastructure issues.

Given JSON with deterministic findings and a resource sample, respond with JSON only:
{
  "summary": "2-4 sentence executive summary",
  "estimated_savings": "human-readable estimate (e.g. '$120/month' or 'Unknown')",
  "enriched_findings": [
    {
      "finding_id": "<must match input finding_id>",
      "ai_explanation": "clear explanation for the user",
      "fix_command": "single copyable AWS CLI command (aws ...), never Azure"
    }
  ]
}

Rules:
- Include one enriched_findings entry per input finding (same finding_id).
- fix_command must be valid AWS CLI using resource region/ids from evidence when possible.
- Do not remove or change severity; explain and remediate only.
- If a finding has no safe CLI fix, set fix_command to null.
"""
