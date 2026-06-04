"""
Amazon RDS PostgreSQL — connection, schema, and analysis persistence (WP3).

Public API for other modules
----------------------------
* ``is_configured()`` — whether ``DATABASE_URL`` is set
* ``init_db()`` — create ``users`` and ``analyses`` tables (idempotent)
* ``save_analysis(user_id, request, response)`` → analysis UUID string
* ``list_analyses(user_id=None, limit=50)`` → history rows for ``GET /api/history``
* ``get_analysis(analysis_id, user_id=None)`` → full row or None for detail views
* ``create_user(email, password_hash)`` / ``get_user_by_email(email)`` — for WP4 auth

``user_id`` is optional until JWT auth (WP4); ``NULL`` rows are shared pre-auth history.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

import psycopg2
import psycopg2.extras

from models.requests import AnalyzeRequest
from models.responses import AnalyzeResponse

logger = logging.getLogger(__name__)

DATABASE_URL_ENV = "DATABASE_URL"


class DatabaseError(Exception):
    def __init__(self, message: str, code: str = "database_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def is_configured() -> bool:
    return bool(os.getenv(DATABASE_URL_ENV, "").strip())


def _require_url() -> str:
    url = os.getenv(DATABASE_URL_ENV, "").strip()
    if not url:
        raise DatabaseError(
            f"{DATABASE_URL_ENV} is not set. Add it to .env for analysis persistence.",
            "database_not_configured",
        )
    return url


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(_require_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist. Safe to call on every app startup."""
    if not is_configured():
        logger.warning(
            "%s not set — skipping database initialization. History API will be unavailable.",
            DATABASE_URL_ENV,
        )
        return

    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            scan_scope JSONB NOT NULL DEFAULT '{}'::jsonb,
            regions_scanned TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
            services_scanned TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
            resources_scanned INTEGER NOT NULL DEFAULT 0,
            issues_found INTEGER NOT NULL DEFAULT 0,
            estimated_savings TEXT,
            analysis_result JSONB NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'completed',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_analyses_user_created
            ON analyses (user_id, created_at DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_analyses_created
            ON analyses (created_at DESC);
        """,
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
    logger.info("Database schema initialized (users, analyses)")


def _build_scan_scope(request: AnalyzeRequest, response: AnalyzeResponse) -> dict[str, Any]:
    return {
        "tags": request.tags,
        "regions": response.regions_scanned,
        "services": response.services_scanned,
        "tags_filter": response.tags_filter,
        "account_id": response.account_id,
    }


def _issues_count(response: AnalyzeResponse) -> int:
    return int(response.findings_summary.get("total", len(response.findings)))


def _estimated_savings(response: AnalyzeResponse) -> str | None:
    if response.ai_enrichment and response.ai_enrichment.estimated_savings:
        return response.ai_enrichment.estimated_savings
    return None


def save_analysis(
    user_id: str | None,
    request: AnalyzeRequest,
    response: AnalyzeResponse,
    status: str = "completed",
) -> str:
    """
    Persist a completed analyze run. Returns the new analysis UUID.

    ``analysis_result`` stores the full ``AnalyzeResponse`` JSON for report/history views.
    """
    analysis_id = str(uuid.uuid4())
    payload = response.model_dump(mode="json")
    scan_scope = _build_scan_scope(request, response)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analyses (
                    id, user_id, scan_scope, regions_scanned, services_scanned,
                    resources_scanned, issues_found, estimated_savings,
                    analysis_result, status
                ) VALUES (
                    %s::uuid, %s::uuid, %s::jsonb, %s, %s,
                    %s, %s, %s, %s::jsonb, %s
                )
                """,
                (
                    analysis_id,
                    user_id,
                    json.dumps(scan_scope),
                    response.regions_scanned,
                    response.services_scanned,
                    response.resource_count,
                    _issues_count(response),
                    _estimated_savings(response),
                    json.dumps(payload),
                    status,
                ),
            )

    logger.info("Saved analysis %s (resources=%s, issues=%s)", analysis_id, response.resource_count, _issues_count(response))
    return analysis_id


def list_analyses(
    user_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List analysis history summaries, newest first.

    When ``user_id`` is None (pre-WP4), returns analyses with ``user_id IS NULL``.
    When ``user_id`` is set (post-auth), returns only that user's rows.
    """
    limit = max(1, min(limit, 100))

    if user_id:
        query = """
            SELECT id, user_id, scan_scope, regions_scanned, services_scanned,
                   resources_scanned, issues_found, estimated_savings, status, created_at
            FROM analyses
            WHERE user_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT %s
        """
        params: tuple[Any, ...] = (user_id, limit)
    else:
        query = """
            SELECT id, user_id, scan_scope, regions_scanned, services_scanned,
                   resources_scanned, issues_found, estimated_savings, status, created_at
            FROM analyses
            WHERE user_id IS NULL
            ORDER BY created_at DESC
            LIMIT %s
        """
        params = (limit,)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [_format_history_row(row) for row in rows]


def get_analysis(
    analysis_id: str,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    """Fetch one analysis including full ``analysis_result`` JSON."""
    if user_id:
        query = """
            SELECT id, user_id, scan_scope, regions_scanned, services_scanned,
                   resources_scanned, issues_found, estimated_savings,
                   analysis_result, status, created_at
            FROM analyses
            WHERE id = %s::uuid AND user_id = %s::uuid
        """
        params: tuple[Any, ...] = (analysis_id, user_id)
    else:
        query = """
            SELECT id, user_id, scan_scope, regions_scanned, services_scanned,
                   resources_scanned, issues_found, estimated_savings,
                   analysis_result, status, created_at
            FROM analyses
            WHERE id = %s::uuid AND user_id IS NULL
        """
        params = (analysis_id,)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()

    if not row:
        return None

    result = _format_history_row(row)
    result["analysis_result"] = row.get("analysis_result")
    return result


def create_user(email: str, password_hash: str) -> str:
    """Insert a user (WP4 signup). Returns user UUID."""
    user_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash)
                VALUES (%s::uuid, %s, %s)
                RETURNING id
                """,
                (user_id, email.lower().strip(), password_hash),
            )
            returned = cur.fetchone()
    return str(returned[0]) if returned else user_id


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Lookup user by email (WP4 login)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, email, password_hash, created_at FROM users WHERE email = %s",
                (email.lower().strip(),),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "password_hash": row["password_hash"],
        "created_at": row["created_at"],
    }


def _format_history_row(row: dict[str, Any]) -> dict[str, Any]:
    created = row.get("created_at")
    if isinstance(created, datetime):
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        created_iso = created.isoformat()
    else:
        created_iso = str(created) if created else None

    scan_scope = row.get("scan_scope") or {}
    if isinstance(scan_scope, str):
        scan_scope = json.loads(scan_scope)

    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]) if row.get("user_id") else None,
        "scan_scope": scan_scope,
        "regions_scanned": list(row.get("regions_scanned") or []),
        "services_scanned": list(row.get("services_scanned") or []),
        "resources_scanned": row.get("resources_scanned", 0),
        "issues_found": row.get("issues_found", 0),
        "estimated_savings": row.get("estimated_savings"),
        "status": row.get("status", "completed"),
        "created_at": created_iso,
        "workload_label": _workload_label(scan_scope),
    }


def _workload_label(scan_scope: dict[str, Any]) -> str:
    tags = scan_scope.get("tags") or scan_scope.get("tags_filter") or {}
    env = tags.get("Environment")
    project = tags.get("Project")
    if env and project:
        return f"{env} / {project}"
    if env:
        return str(env)
    if project:
        return str(project)
    regions = scan_scope.get("regions") or []
    if regions:
        return ", ".join(regions[:3]) + ("…" if len(regions) > 3 else "")
    return "AWS scan"
