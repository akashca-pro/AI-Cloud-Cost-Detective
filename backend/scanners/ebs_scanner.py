from __future__ import annotations

import boto3

from models.resources import CostSignal, NormalizedResource, UtilizationMetrics
from scanners.base import BaseScanner, flatten_aws_tags, tags_match


class EBSScanner(BaseScanner):
    service_name = "ebs"

    def scan_region(
        self,
        session: boto3.Session,
        region: str,
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        ec2 = session.client("ec2", region_name=region)
        paginator = ec2.get_paginator("describe_volumes")
        resources: list[NormalizedResource] = []

        for page in paginator.paginate():
            for volume in page.get("Volumes", []):
                volume_id = volume.get("VolumeId", "")
                if not volume_id:
                    continue
                tags = flatten_aws_tags(volume.get("Tags"))
                if tag_filter and not tags_match(tags, tag_filter):
                    continue

                attachments = volume.get("Attachments", [])
                attached = len(attachments) > 0
                name = tags.get("Name", volume_id)

                resources.append(
                    NormalizedResource(
                        resource_id=volume_id,
                        resource_type="ebs",
                        region=region,
                        name=name,
                        tags=tags,
                        attributes={
                            "size_gib": volume.get("Size"),
                            "volume_type": volume.get("VolumeType"),
                            "state": volume.get("State"),
                            "encrypted": volume.get("Encrypted"),
                            "attached_instance_ids": [
                                a.get("InstanceId") for a in attachments if a.get("InstanceId")
                            ],
                        },
                        cost_signals=CostSignal(
                            billing_category="storage",
                            notes=["ebs_gb_month"],
                        ),
                        utilization_metrics=UtilizationMetrics(attached=attached),
                    )
                )

        return resources
