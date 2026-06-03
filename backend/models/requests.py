from typing import Literal

from pydantic import BaseModel, Field

ServiceName = Literal["ec2", "rds", "s3", "elb", "ebs"]

DEFAULT_SERVICES: list[ServiceName] = ["ec2", "rds", "s3", "elb", "ebs"]


class AnalyzeRequest(BaseModel):
    """AWS-native discovery scope: regions, services, and tag-based workload filters."""

    regions: list[str] | None = Field(
        default=None,
        description="AWS regions to scan. If omitted, all enabled regions are discovered dynamically.",
        examples=[["us-east-1", "us-west-2"]],
    )
    services: list[ServiceName] = Field(
        default_factory=lambda: list(DEFAULT_SERVICES),
        description="Service modules to run (ec2, rds, s3, elb, ebs).",
    )
    tags: dict[str, str] = Field(
        default_factory=dict,
        description="Tag filter (AND). Example: Environment=prod, Project=payments.",
        examples=[{"Environment": "prod", "Project": "payments"}],
    )
