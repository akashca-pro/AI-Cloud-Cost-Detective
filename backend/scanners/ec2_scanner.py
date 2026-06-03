from __future__ import annotations

import boto3

from core.cloudwatch import average_cpu_utilization_7d
from models.resources import CostSignal, NormalizedResource, UtilizationMetrics
from scanners.base import BaseScanner, flatten_aws_tags, tags_match


class EC2Scanner(BaseScanner):
    service_name = "ec2"

    def scan_region(
        self,
        session: boto3.Session,
        region: str,
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        ec2 = session.client("ec2", region_name=region)
        paginator = ec2.get_paginator("describe_instances")
        resources: list[NormalizedResource] = []

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance.get("InstanceId", "")
                    if not instance_id:
                        continue
                    tags = flatten_aws_tags(instance.get("Tags"))
                    if tag_filter and not tags_match(tags, tag_filter):
                        continue

                    name = tags.get("Name", instance_id)
                    state = instance.get("State", {}).get("Name", "unknown")
                    instance_type = instance.get("InstanceType", "")

                    cpu_avg = None
                    if state == "running":
                        cpu_avg = average_cpu_utilization_7d(session, region, instance_id)

                    resources.append(
                        NormalizedResource(
                            resource_id=instance_id,
                            resource_type="ec2",
                            region=region,
                            name=name,
                            arn=instance.get("InstanceArn"),
                            tags=tags,
                            attributes={
                                "instance_type": instance_type,
                                "state": state,
                                "launch_time": instance.get("LaunchTime", "").isoformat()
                                if instance.get("LaunchTime")
                                else None,
                                "vpc_id": instance.get("VpcId"),
                            },
                            cost_signals=CostSignal(
                                billing_category="compute",
                                notes=["ec2_instance_hourly"],
                            ),
                            utilization_metrics=UtilizationMetrics(
                                cpu_avg_percent_7d=cpu_avg,
                            ),
                        )
                    )

        return resources
