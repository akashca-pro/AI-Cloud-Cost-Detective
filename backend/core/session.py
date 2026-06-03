"""Boto3 session and client helpers."""

from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

from core.exceptions import AWSAccessDeniedError, AWSCredentialsError, AWSDiscoveryError

logger = logging.getLogger(__name__)


def create_session(profile: str | None = None) -> boto3.Session:
    if profile:
        return boto3.Session(profile_name=profile)
    return boto3.Session()


def wrap_client_error(exc: ClientError, context: str) -> AWSDiscoveryError:
    code = exc.response.get("Error", {}).get("Code", "Unknown")
    message = exc.response.get("Error", {}).get("Message", str(exc))
    detail = f"{context}: {code} — {message}"

    if code in {
        "UnauthorizedOperation",
        "AccessDenied",
        "AccessDeniedException",
        "AllAccessDisabled",
    }:
        return AWSAccessDeniedError(detail)
    return AWSDiscoveryError(detail, "aws_api_error")


def client(
    session: boto3.Session,
    service: str,
    region: str | None = None,
) -> Any:
    return session.client(service, region_name=region) if region else session.client(service)


def safe_boto3_call(context: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except (NoCredentialsError, PartialCredentialsError) as exc:
        raise AWSCredentialsError(str(exc)) from exc
    except ClientError as exc:
        raise wrap_client_error(exc, context) from exc
