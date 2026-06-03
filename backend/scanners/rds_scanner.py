from __future__ import annotations

import boto3

from models.resources import CostSignal, NormalizedResource
from scanners.base import BaseScanner, flatten_aws_tags, tags_match


class RDSScanner(BaseScanner):
    service_name = "rds"

    def scan_region(
        self,
        session: boto3.Session,
        region: str,
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        rds = session.client("rds", region_name=region)
        paginator = rds.get_paginator("describe_db_instances")
        resources: list[NormalizedResource] = []

        for page in paginator.paginate():
            for db in page.get("DBInstances", []):
                db_id = db.get("DBInstanceIdentifier", "")
                if not db_id:
                    continue
                arn = db.get("DBInstanceArn")
                tags = self._fetch_instance_tags(rds, arn) if arn else {}
                if tag_filter and not tags_match(tags, tag_filter):
                    continue

                resources.append(
                    NormalizedResource(
                        resource_id=db_id,
                        resource_type="rds",
                        region=region,
                        name=db_id,
                        arn=arn,
                        tags=tags,
                        attributes={
                            "engine": db.get("Engine"),
                            "engine_version": db.get("EngineVersion"),
                            "instance_class": db.get("DBInstanceClass"),
                            "multi_az": db.get("MultiAZ"),
                            "storage_type": db.get("StorageType"),
                            "allocated_storage_gib": db.get("AllocatedStorage"),
                            "status": db.get("DBInstanceStatus"),
                        },
                        cost_signals=CostSignal(
                            billing_category="database",
                            notes=["rds_instance_hourly", "rds_storage_gb_month"],
                        ),
                    )
                )

        return resources

    def _fetch_instance_tags(self, rds_client: boto3.client, arn: str) -> dict[str, str]:
        try:
            response = rds_client.list_tags_for_resource(ResourceName=arn)
            return flatten_aws_tags(response.get("TagList"))
        except Exception:
            return {}
