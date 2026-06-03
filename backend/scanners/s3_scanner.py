from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from models.resources import CostSignal, NormalizedResource, UtilizationMetrics
from scanners.base import BaseScanner, flatten_aws_tags, tags_match


class S3Scanner(BaseScanner):
    """S3 is global; bucket location determines regional assignment."""

    service_name = "s3"

    def scan(
        self,
        session: boto3.Session,
        regions: list[str],
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        region_set = set(regions)
        s3 = session.client("s3")
        resources: list[NormalizedResource] = []
        for bucket in s3.list_buckets().get("Buckets", []):
            bucket_name = bucket.get("Name", "")
            if not bucket_name:
                continue
            bucket_region = self._bucket_region(s3, bucket_name)
            if bucket_region not in region_set:
                continue
            tags = self._bucket_tags(s3, bucket_name)
            if tag_filter and not tags_match(tags, tag_filter):
                continue
            resources.append(
                NormalizedResource(
                    resource_id=bucket_name,
                    resource_type="s3",
                    region=bucket_region,
                    name=bucket_name,
                    arn=f"arn:aws:s3:::{bucket_name}",
                    tags=tags,
                    attributes={
                        "creation_date": bucket.get("CreationDate", "").isoformat()
                        if bucket.get("CreationDate")
                        else None,
                    },
                    cost_signals=CostSignal(
                        billing_category="storage",
                        notes=["s3_storage_gb_month", "s3_requests"],
                    ),
                    utilization_metrics=UtilizationMetrics(
                        has_lifecycle_policy=self._has_lifecycle_policy(s3, bucket_name),
                    ),
                )
            )
        return resources

    def scan_region(
        self,
        session: boto3.Session,
        region: str,
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        return self.scan(session, [region], tag_filter)

    def _bucket_region(self, s3_client: boto3.client, bucket_name: str) -> str:
        try:
            loc = s3_client.get_bucket_location(Bucket=bucket_name)
            region = loc.get("LocationConstraint")
            return region or "us-east-1"
        except ClientError:
            return "us-east-1"

    def _bucket_tags(self, s3_client: boto3.client, bucket_name: str) -> dict[str, str]:
        try:
            response = s3_client.get_bucket_tagging(Bucket=bucket_name)
            return flatten_aws_tags(response.get("TagSet"))
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchTagSet", "AccessDenied"):
                return {}
            return {}
        except Exception:
            return {}

    def _has_lifecycle_policy(self, s3_client: boto3.client, bucket_name: str) -> bool:
        try:
            s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchLifecycleConfiguration", "NoSuchLifecycleConfigurationRule"):
                return False
            return False
        except Exception:
            return False
