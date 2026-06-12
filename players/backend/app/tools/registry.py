"""Assistant tool registry (CONTRACT.md §7) — the fixed operation set."""

from __future__ import annotations

import inspect

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.tools import (
    filtered_list,
    mental_profile_query,
    nfl_outcome_lookup,
    player_compare,
    player_profile,
    production_lookup,
    report_search,
    role_search,
    scheme_fit,
    scout_comment,
    similarity_comparison,
    team_fit,
)

_MODULES = [
    filtered_list,
    player_profile,
    report_search,
    similarity_comparison,
    scout_comment,
    scheme_fit,
    role_search,
    mental_profile_query,
    production_lookup,
    nfl_outcome_lookup,
    team_fit,
    player_compare,
]

TOOLS = [m.TOOL for m in _MODULES]
_RUNNERS = {m.TOOL["name"]: m.run for m in _MODULES}


async def run_tool(
    session: AsyncSession, name: str, args: dict, user_id: str = "assistant"
) -> dict:
    runner = _RUNNERS.get(name)
    if runner is None:
        return {"error": f"unknown tool '{name}'", "detail": f"unknown tool '{name}'"}
    try:
        if "user_id" in inspect.signature(runner).parameters:
            return await runner(session, args or {}, user_id=user_id)
        return await runner(session, args or {})
    except Exception as exc:  # tool failures must not kill the chat stream
        return {"error": f"{type(exc).__name__}: {exc}", "detail": f"{name} failed"}
