from pydantic import BaseModel, Field

from models.resources import Finding, NormalizedResource


class WorkloadSummary(BaseModel):
    """Logical workload bucket derived from tags (e.g. Environment + Project)."""

    workload_key: str
    environment: str | None = None
    project: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    resource_count: int = 0
    resource_ids: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    cloud_provider: str = "aws"
    account_id: str | None = None
    regions_scanned: list[str] = Field(default_factory=list)
    services_scanned: list[str] = Field(default_factory=list)
    tags_filter: dict[str, str] = Field(default_factory=dict)
    resource_count: int = 0
    resources: list[NormalizedResource] = Field(default_factory=list)
    workloads: list[WorkloadSummary] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    findings_summary: dict[str, int] = Field(default_factory=dict)
