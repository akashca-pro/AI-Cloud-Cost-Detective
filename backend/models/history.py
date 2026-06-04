from typing import Any

from pydantic import BaseModel, Field

from models.responses import AnalyzeResponse


class AnalysisHistoryItem(BaseModel):
    id: str
    user_id: str | None = None
    scan_scope: dict[str, Any] = Field(default_factory=dict)
    regions_scanned: list[str] = Field(default_factory=list)
    services_scanned: list[str] = Field(default_factory=list)
    resources_scanned: int = 0
    issues_found: int = 0
    estimated_savings: str | None = None
    status: str = "completed"
    created_at: str | None = None
    workload_label: str = ""


class AnalysisHistoryDetail(AnalysisHistoryItem):
    analysis_result: AnalyzeResponse | dict[str, Any] | None = None


class HistoryListResponse(BaseModel):
    cloud_provider: str = "aws"
    count: int = 0
    analyses: list[AnalysisHistoryItem] = Field(default_factory=list)


class HistoryDetailResponse(BaseModel):
    cloud_provider: str = "aws"
    analysis: AnalysisHistoryDetail
