from __future__ import annotations

import boto3

from models.resources import CostSignal, NormalizedResource, UtilizationMetrics
from scanners.base import BaseScanner, flatten_aws_tags, tags_match


class ELBScanner(BaseScanner):
    service_name = "elb"

    def scan_region(
        self,
        session: boto3.Session,
        region: str,
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        elbv2 = session.client("elbv2", region_name=region)
        paginator = elbv2.get_paginator("describe_load_balancers")
        resources: list[NormalizedResource] = []

        for page in paginator.paginate():
            for lb in page.get("LoadBalancers", []):
                lb_arn = lb.get("LoadBalancerArn", "")
                lb_name = lb.get("LoadBalancerName", lb_arn)
                if not lb_arn:
                    continue

                tags = self._fetch_tags(elbv2, lb_arn)
                if tag_filter and not tags_match(tags, tag_filter):
                    continue

                healthy_targets = self._count_healthy_targets(elbv2, lb_arn)

                resources.append(
                    NormalizedResource(
                        resource_id=lb_name,
                        resource_type="elb",
                        region=region,
                        name=lb_name,
                        arn=lb_arn,
                        tags=tags,
                        attributes={
                            "scheme": lb.get("Scheme"),
                            "type": lb.get("Type"),
                            "dns_name": lb.get("DNSName"),
                            "state": lb.get("State", {}).get("Code"),
                        },
                        cost_signals=CostSignal(
                            billing_category="network",
                            notes=["elb_lcu_hourly"],
                        ),
                        utilization_metrics=UtilizationMetrics(
                            healthy_target_count=healthy_targets,
                        ),
                    )
                )

        return resources

    def _fetch_tags(self, client: boto3.client, arn: str) -> dict[str, str]:
        try:
            response = client.describe_tags(ResourceArns=[arn])
            tag_list = response.get("TagDescriptions", [{}])[0].get("Tags", [])
            return flatten_aws_tags(tag_list)
        except Exception:
            return {}

    def _count_healthy_targets(self, client: boto3.client, lb_arn: str) -> int:
        healthy = 0
        try:
            tgs = client.describe_target_groups(LoadBalancerArn=lb_arn)
            for tg in tgs.get("TargetGroups", []):
                tg_arn = tg.get("TargetGroupArn")
                if not tg_arn:
                    continue
                health = client.describe_target_health(TargetGroupArn=tg_arn)
                for target in health.get("TargetHealthDescriptions", []):
                    if target.get("TargetHealth", {}).get("State") == "healthy":
                        healthy += 1
        except Exception:
            return 0
        return healthy
