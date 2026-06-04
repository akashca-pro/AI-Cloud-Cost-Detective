"""AI Cloud Cost Detective — AWS-native FinOps discovery API."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.exceptions import (
    AWSAccessDeniedError,
    AWSCredentialsError,
    AWSDiscoveryError,
    AWSRegionError,
)
from models.requests import AnalyzeRequest
from models.responses import AnalyzeResponse
from services.aws_discovery_service import AWSDiscoveryService

app = FastAPI(
    title="AI Cloud Cost Detective",
    description="AWS-native infrastructure discovery and deterministic FinOps detection",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _http_error(exc: AWSDiscoveryError) -> HTTPException:
    status_map = {
        "aws_credentials_not_configured": 503,
        "aws_access_denied": 403,
        "aws_region_error": 400,
        "invalid_service": 400,
        "aws_region_enumeration_failed": 502,
    }
    return HTTPException(
        status_code=status_map.get(exc.code, 502),
        detail={"detail": exc.message, "code": exc.code},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "cloud_provider": "aws"}


@app.get("/api/aws/regions")
async def list_enabled_regions() -> dict:
    """Dynamically list enabled AWS regions for the configured account."""
    service = AWSDiscoveryService()
    try:
        regions = service.discover_enabled_regions()
    except AWSCredentialsError as exc:
        raise _http_error(exc) from exc
    except AWSDiscoveryError as exc:
        raise _http_error(exc) from exc

    return {
        "cloud_provider": "aws",
        "regions": regions,
        "count": len(regions),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Discover AWS resources by region, service, and tags; run deterministic FinOps checks;
    enrich results with OpenAI summary and AWS CLI remediation hints.

    Example workload filter:
    ``{"tags": {"Environment": "prod", "Project": "payments"}}``
    """
    if not request.services:
        raise HTTPException(
            status_code=400,
            detail={"detail": "At least one service is required.", "code": "invalid_request"},
        )

    service = AWSDiscoveryService()
    try:
        return await service.analyze(request)
    except AWSCredentialsError as exc:
        raise _http_error(exc) from exc
    except AWSAccessDeniedError as exc:
        raise _http_error(exc) from exc
    except AWSRegionError as exc:
        raise _http_error(exc) from exc
    except AWSDiscoveryError as exc:
        raise _http_error(exc) from exc
