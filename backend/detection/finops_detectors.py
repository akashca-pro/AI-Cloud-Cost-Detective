"""Deterministic FinOps detection — no AI required for discovery or findings."""

from __future__ import annotations

import hashlib

from models.resources import Finding, NormalizedResource

LOW_CPU_THRESHOLD_PERCENT = 10.0


class FinOpsDetector:
    """Run rule-based checks on normalized resources."""

    def detect(self, resources: list[NormalizedResource]) -> list[Finding]:
        findings: list[Finding] = []
        for resource in resources:
            findings.extend(self._detect_resource(resource))
        return findings

    def _detect_resource(self, resource: NormalizedResource) -> list[Finding]:
        dispatch = {
            "ec2": self._detect_ec2,
            "ebs": self._detect_ebs,
            "elb": self._detect_elb,
            "s3": self._detect_s3,
            "rds": self._detect_rds,
        }
        handler = dispatch.get(resource.resource_type)
        if handler:
            return handler(resource)
        return []

    def _finding(
        self,
        resource: NormalizedResource,
        category: str,
        severity: str,
        title: str,
        description: str,
        evidence: dict,
        recommendation_hint: str,
    ) -> Finding:
        raw = f"{category}:{resource.resource_id}:{title}"
        finding_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return Finding(
            finding_id=finding_id,
            severity=severity,  # type: ignore[arg-type]
            category=category,
            title=title,
            description=description,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            region=resource.region,
            evidence=evidence,
            recommendation_hint=recommendation_hint,
        )

    def _detect_ec2(self, resource: NormalizedResource) -> list[Finding]:
        findings: list[Finding] = []
        state = resource.attributes.get("state")
        cpu = resource.utilization_metrics.cpu_avg_percent_7d

        if state == "running" and cpu is not None and cpu < LOW_CPU_THRESHOLD_PERCENT:
            findings.append(
                self._finding(
                    resource,
                    category="over_provisioning",
                    severity="medium",
                    title="Low EC2 CPU utilization",
                    description=(
                        f"Instance {resource.resource_id} averaged {cpu}% CPU over 7 days, "
                        f"below {LOW_CPU_THRESHOLD_PERCENT}% threshold."
                    ),
                    evidence={"cpu_avg_percent_7d": cpu, "instance_type": resource.attributes.get("instance_type")},
                    recommendation_hint="Consider rightsizing, stopping non-prod instances, or using Auto Scaling.",
                )
            )

        if state == "stopped":
            findings.append(
                self._finding(
                    resource,
                    category="idle_resource",
                    severity="low",
                    title="Stopped EC2 instance still incurring EBS costs",
                    description=f"Instance {resource.resource_id} is stopped; attached EBS volumes may still bill.",
                    evidence={"state": state},
                    recommendation_hint="Terminate unused instances and delete unattached volumes.",
                )
            )

        return findings

    def _detect_ebs(self, resource: NormalizedResource) -> list[Finding]:
        if resource.utilization_metrics.attached is False:
            return [
                self._finding(
                    resource,
                    category="unused_resource",
                    severity="high",
                    title="Unattached EBS volume",
                    description=f"Volume {resource.resource_id} has no attachments and continues to incur storage cost.",
                    evidence={
                        "size_gib": resource.attributes.get("size_gib"),
                        "volume_type": resource.attributes.get("volume_type"),
                    },
                    recommendation_hint="Snapshot if needed, then delete the volume.",
                )
            ]
        return []

    def _detect_elb(self, resource: NormalizedResource) -> list[Finding]:
        healthy = resource.utilization_metrics.healthy_target_count
        if healthy is not None and healthy == 0:
            return [
                self._finding(
                    resource,
                    category="idle_resource",
                    severity="medium",
                    title="Idle load balancer (no healthy targets)",
                    description=f"Load balancer {resource.name} has zero healthy registered targets.",
                    evidence={"healthy_target_count": healthy, "dns_name": resource.attributes.get("dns_name")},
                    recommendation_hint="Remove unused load balancers or register targets.",
                )
            ]
        return []

    def _detect_s3(self, resource: NormalizedResource) -> list[Finding]:
        if resource.utilization_metrics.has_lifecycle_policy is False:
            return [
                self._finding(
                    resource,
                    category="misconfiguration",
                    severity="medium",
                    title="S3 bucket missing lifecycle policy",
                    description=f"Bucket {resource.resource_id} has no lifecycle rules for tiering or expiration.",
                    evidence={"has_lifecycle_policy": False},
                    recommendation_hint="Add lifecycle rules to transition to IA/Glacier or expire old objects.",
                )
            ]
        return []

    def _detect_rds(self, resource: NormalizedResource) -> list[Finding]:
        findings: list[Finding] = []
        if resource.attributes.get("multi_az") and resource.attributes.get("instance_class", "").startswith("db."):
            # Heuristic: very large dev/test instances — only flag if Environment tag suggests non-prod
            env = resource.tags.get("Environment", "").lower()
            if env in ("dev", "development", "test", "staging") and "xlarge" in resource.attributes.get("instance_class", ""):
                findings.append(
                    self._finding(
                        resource,
                        category="over_provisioning",
                        severity="medium",
                        title="Large RDS instance in non-production environment",
                        description=(
                            f"RDS {resource.resource_id} uses {resource.attributes.get('instance_class')} "
                            f"with Environment={resource.tags.get('Environment')}."
                        ),
                        evidence={
                            "instance_class": resource.attributes.get("instance_class"),
                            "environment": resource.tags.get("Environment"),
                        },
                        recommendation_hint="Rightsize RDS or use Aurora Serverless for variable workloads.",
                    )
                )
        return findings

    @staticmethod
    def summarize(findings: list[Finding]) -> dict[str, int]:
        summary = {"high": 0, "medium": 0, "low": 0, "total": len(findings)}
        for f in findings:
            summary[f.severity] = summary.get(f.severity, 0) + 1
        return summary
