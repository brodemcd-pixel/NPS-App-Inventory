"""Slack -> web identity passthrough tokens (CONTRACT.md §6 auth, §9)."""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.app.config import settings

SALT = "slack-link"
MAX_AGE_SECONDS = 600


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt=SALT)


def sign_slack_user(user_id: str, name: str | None = None) -> str:
    return _serializer().dumps({"user_id": user_id, "name": name})


def verify_slack_token(token: str) -> dict | None:
    """Returns {"user_id", "name"} or None when invalid/expired."""
    try:
        data = _serializer().loads(token, max_age=MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict) or "user_id" not in data:
        return None
    return {"user_id": data["user_id"], "name": data.get("name")}
