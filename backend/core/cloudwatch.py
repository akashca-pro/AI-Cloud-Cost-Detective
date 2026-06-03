"""CloudWatch metric helpers for utilization-based detection."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def average_cpu_utilization_7d(
    session: boto3.Session,
    region: str,
    instance_id: str,
) -> float | None:
    """Return average EC2 CPUUtilization (%) over the last 7 days, or None if unavailable."""
    cw = session.client("cloudwatch", region_name=region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    try:
        response = cw.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start,
            EndTime=end,
            Period=3600,
            Statistics=["Average"],
        )
    except ClientError as exc:
        logger.debug("CloudWatch CPU metric unavailable for %s: %s", instance_id, exc)
        return None

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    values = [dp["Average"] for dp in datapoints if "Average" in dp]
    if not values:
        return None
    return round(sum(values) / len(values), 2)
