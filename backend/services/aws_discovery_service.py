"""Core AWS discovery orchestration: regions, scanners, workloads, detection."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from core.exceptions import AWSCredentialsError, AWSRegionError, AWSDiscoveryError
from core.session import create_session
from detection.finops_detectors import FinOpsDetector
from models.requests import AnalyzeRequest
from models.resources import NormalizedResource
from models.responses import AnalyzeResponse, WorkloadSummary
from scanners import SCANNER_REGISTRY
from scanners.base import BaseScanner

logger = logging.getLogger(__name__)

OPTED_IN_STATUSES = {"opt-in-not-required", "opted-in", "enabled-by-default"}


class AWSDiscoveryService:
    def __init__(self, session: boto3.Session | None = None) -> None:
        self.session = session or create_session()
        self.detector = FinOpsDetector()

    def get_account_id(self) -> str | None:
        try:
            sts = self.session.client("sts")
            return sts.get_caller_identity().get("Account")
        except (NoCredentialsError, PartialCredentialsError) as exc:
            raise AWSCredentialsError(str(exc)) from exc
        except ClientError:
            return None

    def discover_enabled_regions(self, requested: list[str] | None = None) -> list[str]:
        try:
            ec2 = self.session.client("ec2", region_name="us-east-1")
            response = ec2.describe_regions(AllRegions=True)
        except (NoCredentialsError, PartialCredentialsError) as exc:
            raise AWSCredentialsError(str(exc)) from exc
        except ClientError as exc:
            raise AWSDiscoveryError(
                f"Failed to enumerate AWS regions: {exc}",
                "aws_region_enumeration_failed",
            ) from exc

        enabled = [
            r["RegionName"]
            for r in response.get("Regions", [])
            if r.get("RegionName")
            and (r.get("OptInStatus") in OPTED_IN_STATUSES or not r.get("OptInStatus"))
        ]
        enabled.sort()

        if requested:
            unknown = [r for r in requested if r not in enabled]
            if unknown:
                raise AWSRegionError(
                    f"Requested regions are not enabled in this account: {', '.join(unknown)}"
                )
            return requested

        return enabled

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        regions = self.discover_enabled_regions(request.regions)
        services = list(dict.fromkeys(request.services))  # preserve order, dedupe
        tag_filter = request.tags

        resources = await self._scan_all(services, regions, tag_filter)
        workloads = self._aggregate_workloads(resources, tag_filter)
        findings = self.detector.detect(resources)

        return AnalyzeResponse(
            cloud_provider="aws",
            account_id=self.get_account_id(),
            regions_scanned=regions,
            services_scanned=services,
            tags_filter=tag_filter,
            resource_count=len(resources),
            resources=resources,
            workloads=workloads,
            findings=findings,
            findings_summary=self.detector.summarize(findings),
        )

    async def _scan_all(
        self,
        services: list[str],
        regions: list[str],
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        tasks = []
        for service in services:
            scanner = SCANNER_REGISTRY.get(service)
            if not scanner:
                raise AWSDiscoveryError(
                    f"Unknown service '{service}'. Supported: {', '.join(sorted(SCANNER_REGISTRY))}",
                    "invalid_service",
                )
            tasks.append(
                asyncio.to_thread(self._run_scanner, scanner, regions, tag_filter)
            )

        results = await asyncio.gather(*tasks)
        merged: list[NormalizedResource] = []
        for batch in results:
            merged.extend(batch)
        return merged

    def _run_scanner(
        self,
        scanner: BaseScanner,
        regions: list[str],
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        logger.info("Scanning %s across %d region(s)", scanner.service_name, len(regions))
        return scanner.scan(self.session, regions, tag_filter)

    def _aggregate_workloads(
        self,
        resources: list[NormalizedResource],
        tag_filter: dict[str, str],
    ) -> list[WorkloadSummary]:
        """Group resources into logical workloads using Environment and Project tags."""
        buckets: dict[str, list[NormalizedResource]] = defaultdict(list)

        for resource in resources:
            env = resource.tags.get("Environment", tag_filter.get("Environment", ""))
            project = resource.tags.get("Project", tag_filter.get("Project", ""))
            if env or project:
                key = f"Environment={env or '*'},Project={project or '*'}"
            elif tag_filter:
                key = ",".join(f"{k}={v}" for k, v in sorted(tag_filter.items()))
            else:
                key = "ungrouped"
            buckets[key].append(resource)

        workloads: list[WorkloadSummary] = []
        for key, group in sorted(buckets.items()):
            env = group[0].tags.get("Environment") if group else None
            project = group[0].tags.get("Project") if group else None
            tag_snapshot = {}
            if env:
                tag_snapshot["Environment"] = env
            if project:
                tag_snapshot["Project"] = project

            workloads.append(
                WorkloadSummary(
                    workload_key=key,
                    environment=env,
                    project=project,
                    tags=tag_snapshot,
                    resource_count=len(group),
                    resource_ids=[r.resource_id for r in group],
                )
            )
        return workloads
