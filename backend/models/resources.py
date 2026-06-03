from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["high", "medium", "low"]


class CostSignal(BaseModel):
    """Deterministic cost-related signals attached during discovery/detection."""

    model_config = {"extra": "allow"}

    estimated_monthly_waste_usd: float | None = None
    billing_category: str | None = None
    notes: list[str] = Field(default_factory=list)


class UtilizationMetrics(BaseModel):
    """Observed utilization (CloudWatch or service-native heuristics)."""

    model_config = {"extra": "allow"}

    cpu_avg_percent_7d: float | None = None
    attached: bool | None = None
    healthy_target_count: int | None = None
    has_lifecycle_policy: bool | None = None


class NormalizedResource(BaseModel):
    resource_id: str
    resource_type: str
    region: str
    name: str
    arn: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    cost_signals: CostSignal = Field(default_factory=CostSignal)
    utilization_metrics: UtilizationMetrics = Field(default_factory=UtilizationMetrics)


class Finding(BaseModel):
    """Deterministic FinOps finding (AI explains these later, does not discover them)."""

    finding_id: str
    severity: Severity
    category: str
    title: str
    description: str
    resource_id: str
    resource_type: str
    region: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommendation_hint: str | None = None
