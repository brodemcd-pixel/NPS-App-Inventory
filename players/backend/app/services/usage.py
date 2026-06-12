"""Best-effort usage-event logging (CONTRACT.md §6 usage logging).

Uses its own session so a logging failure can never poison a request transaction.
"""

from __future__ import annotations

import logging

from backend.app.db import async_session
from backend.app.models import UsageEvent

logger = logging.getLogger(__name__)


async def log_event(event_type: str, payload: dict | None = None,
                    user_id: str | None = None) -> None:
    try:
        async with async_session() as session:
            session.add(
                UsageEvent(event_type=event_type, payload=payload or {}, user_id=user_id)
            )
            await session.commit()
    except Exception:  # pragma: no cover - logging must never break a request
        logger.warning("usage-event logging failed", exc_info=True)
