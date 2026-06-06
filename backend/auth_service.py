"""JWT signup/login (WP4)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

import db
from db import DatabaseError

JWT_SECRET_ENV = "JWT_SECRET"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


class AuthConfigError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class AuthError(Exception):
    def __init__(self, message: str, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class AuthTokenError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def _jwt_secret() -> str:
    secret = os.getenv(JWT_SECRET_ENV, "").strip()
    if not secret:
        raise AuthConfigError(
            f"{JWT_SECRET_ENV} is not set. Add it to .env for authentication.",
            "jwt_secret_not_configured",
        )
    return secret


def require_auth_configured() -> None:
    if not db.is_configured():
        raise DatabaseError(
            "DATABASE_URL is not configured. Set it in .env to use authentication.",
            "database_not_configured",
        )
    _jwt_secret()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Validate JWT and return payload (WP7)."""
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthTokenError("Token has expired.", "token_expired", 401) from exc
    except jwt.InvalidTokenError as exc:
        raise AuthTokenError("Invalid or missing token.", "invalid_token", 401) from exc


def get_user_id_from_token(token: str) -> str:
    """Extract user UUID from Bearer token."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthTokenError("Invalid token payload.", "invalid_token", 401)
    return str(user_id)


def signup(email: str, password: str) -> str:
    require_auth_configured()
    normalized = email.lower().strip()
    if db.get_user_by_email(normalized):
        raise AuthError("An account with this email already exists.", "email_already_registered", 409)

    password_hash = hash_password(password)
    user_id = db.create_user(normalized, password_hash)
    return create_access_token(user_id, normalized)


def login(email: str, password: str) -> str:
    require_auth_configured()
    normalized = email.lower().strip()
    user = db.get_user_by_email(normalized)
    if not user or not verify_password(password, user["password_hash"]):
        raise AuthError("Invalid email or password.", "invalid_credentials", 401)

    return create_access_token(user["id"], user["email"])
