"""Base scanner contract for regional, tag-filtered boto3 discovery."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import boto3

from models.resources import NormalizedResource


def flatten_aws_tags(tag_list: list[dict[str, str]] | None) -> dict[str, str]:
    if not tag_list:
        return {}
    return {t["Key"]: t["Value"] for t in tag_list if "Key" in t and "Value" in t}


def tags_match(resource_tags: dict[str, str], filter_tags: dict[str, str]) -> bool:
    """All filter tag keys must match exactly (AND semantics)."""
    if not filter_tags:
        return True
    for key, value in filter_tags.items():
        if resource_tags.get(key) != value:
            return False
    return True


class BaseScanner(ABC):
    service_name: str

    @abstractmethod
    def scan_region(
        self,
        session: boto3.Session,
        region: str,
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        """Discover resources in a single region."""

    def scan(
        self,
        session: boto3.Session,
        regions: list[str],
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        resources: list[NormalizedResource] = []
        for region in regions:
            resources.extend(self.scan_region(session, region, tag_filter))
        return resources

    def _filter_by_tags(
        self,
        resources: list[NormalizedResource],
        tag_filter: dict[str, str],
    ) -> list[NormalizedResource]:
        if not tag_filter:
            return resources
        return [r for r in resources if tags_match(r.tags, tag_filter)]

    def _paginate(self, paginator: Any, operation: str, **kwargs: Any) -> list[dict[str, Any]]:
        pages = paginator.paginate(**kwargs)
        items: list[dict[str, Any]] = []
        for page in pages:
            for key, value in page.items():
                if key in ("ResponseMetadata", "NextToken"):
                    continue
                if isinstance(value, list):
                    items.extend(value)
        return items
