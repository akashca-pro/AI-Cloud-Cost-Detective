"""AI Cloud Cost Detective — AWS-native FinOps discovery API."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import db
from core.exceptions import (
    AWSAccessDeniedError,
    AWSCredentialsError,
    AWSDiscoveryError,
    AWSRegionError,
)
from db import DatabaseError
import auth_service
from auth_service import AuthConfigError, AuthError
from models.auth import AuthRequest, AuthResponse
from models.history import AnalysisHistoryDetail, AnalysisHistoryItem, HistoryDetailResponse, HistoryListResponse
from models.requests import AnalyzeRequest
from models.responses import AnalyzeResponse
from progress_hub import ProgressReporter, progress_hub
from services.aws_discovery_service import AWSDiscoveryService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if db.is_configured():
        await asyncio.to_thread(db.init_db)
    yield


app = FastAPI(
    title="AI Cloud Cost Detective",
    description="AWS-native infrastructure discovery, FinOps detection, and analysis history",
    version="0.5.0",
    lifespan=lifespan,
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


def _db_http_error(exc: DatabaseError) -> HTTPException:
    status_map = {
        "database_not_configured": 503,
    }
    return HTTPException(
        status_code=status_map.get(exc.code, 500),
        detail={"detail": exc.message, "code": exc.code},
    )


def _require_db() -> None:
    if not db.is_configured():
        raise DatabaseError(
            "DATABASE_URL is not configured. Set it in .env to use analysis history.",
            "database_not_configured",
        )


def _auth_http_error(exc: AuthError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"detail": exc.message, "code": exc.code},
    )


@app.post("/api/auth/signup", response_model=AuthResponse)
async def auth_signup(body: AuthRequest) -> AuthResponse:
    """Register a user (bcrypt password hash) and return a JWT."""
    try:
        token = await asyncio.to_thread(auth_service.signup, body.email, body.password)
    except AuthConfigError as exc:
        raise HTTPException(
            status_code=503,
            detail={"detail": exc.message, "code": exc.code},
        ) from exc
    except DatabaseError as exc:
        raise _db_http_error(exc) from exc
    except AuthError as exc:
        raise _auth_http_error(exc) from exc

    return AuthResponse(token=token)


@app.post("/api/auth/login", response_model=AuthResponse)
async def auth_login(body: AuthRequest) -> AuthResponse:
    """Validate credentials and return a JWT."""
    try:
        token = await asyncio.to_thread(auth_service.login, body.email, body.password)
    except AuthConfigError as exc:
        raise HTTPException(
            status_code=503,
            detail={"detail": exc.message, "code": exc.code},
        ) from exc
    except DatabaseError as exc:
        raise _db_http_error(exc) from exc
    except AuthError as exc:
        raise _auth_http_error(exc) from exc

    return AuthResponse(token=token)


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "cloud_provider": "aws",
        "database_configured": db.is_configured(),
    }


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


@app.websocket("/ws/progress/{analysis_id}")
async def ws_progress(websocket: WebSocket, analysis_id: str) -> None:
    """Stream live progress for a running or completed analysis."""
    await progress_hub.listen(analysis_id, websocket)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Discover AWS resources by region, service, and tags; run deterministic FinOps checks;
    enrich with OpenAI; persist to PostgreSQL when DATABASE_URL is set.

    Connect to ``ws://localhost:8000/ws/progress/{analysis_id}`` before or during this
    request. Pass the same ``analysis_id`` in the request body (or omit it to let the
    server generate one).
    """
    if not request.services:
        raise HTTPException(
            status_code=400,
            detail={"detail": "At least one service is required.", "code": "invalid_request"},
        )

    analysis_id = request.analysis_id or str(uuid.uuid4())
    reporter = ProgressReporter(progress_hub, analysis_id)

    service = AWSDiscoveryService()
    try:
        response = await service.analyze(request, reporter=reporter)
    except AWSCredentialsError as exc:
        await reporter.emit("error", exc.message, status="error")
        raise _http_error(exc) from exc
    except AWSAccessDeniedError as exc:
        await reporter.emit("error", exc.message, status="error")
        raise _http_error(exc) from exc
    except AWSRegionError as exc:
        await reporter.emit("error", exc.message, status="error")
        raise _http_error(exc) from exc
    except AWSDiscoveryError as exc:
        await reporter.emit("error", exc.message, status="error")
        raise _http_error(exc) from exc
    except Exception as exc:
        await reporter.emit("error", str(exc), status="error")
        raise

    response.analysis_id = analysis_id

    if db.is_configured():
        try:
            await reporter.emit("storing", "Storing results...")
            # user_id wired in WP4 after JWT auth
            await asyncio.to_thread(
                db.save_analysis,
                None,
                request,
                response,
                "completed",
                analysis_id,
            )
        except DatabaseError as exc:
            logger.error("Failed to persist analysis: %s", exc.message)
            await reporter.emit("error", exc.message, status="error")
            raise _db_http_error(exc) from exc

    await reporter.emit("complete", "Analysis complete", status="complete")
    return response


@app.get("/api/history", response_model=HistoryListResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str | None = Query(
        default=None,
        description="Filter by user (JWT auth in WP4). Omit for pre-auth shared history.",
    ),
) -> HistoryListResponse:
    """List past analyses (summary rows). Full report via GET /api/history/{analysis_id}."""
    _require_db()
    try:
        rows = await asyncio.to_thread(db.list_analyses, user_id, limit)
    except DatabaseError as exc:
        raise _db_http_error(exc) from exc

    return HistoryListResponse(
        count=len(rows),
        analyses=[AnalysisHistoryItem.model_validate(row) for row in rows],
    )


@app.get("/api/history/{analysis_id}", response_model=HistoryDetailResponse)
async def get_history_detail(
    analysis_id: str,
    user_id: str | None = Query(default=None),
) -> HistoryDetailResponse:
    """Return one stored analysis including full analysis_result for the report page."""
    _require_db()
    try:
        row = await asyncio.to_thread(db.get_analysis, analysis_id, user_id)
    except DatabaseError as exc:
        raise _db_http_error(exc) from exc

    if not row:
        raise HTTPException(
            status_code=404,
            detail={"detail": f"Analysis '{analysis_id}' not found.", "code": "analysis_not_found"},
        )

    return HistoryDetailResponse(analysis=AnalysisHistoryDetail.model_validate(row))
