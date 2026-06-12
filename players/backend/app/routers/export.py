"""Export endpoints (PDR U3): XLSX always, PDF when WeasyPrint is installed."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.models import Player
from backend.app.routers.players import list_params
from backend.app.services import exporting, similarity, usage
from backend.app.services.details import player_detail
from backend.app.services.players_query import player_summaries, run_player_query

router = APIRouter()

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/export/players.xlsx")
async def export_players_xlsx(
    params: dict = Depends(list_params),
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> Response:
    params["page_size"] = 200
    players, _total = await run_player_query(session, params)
    summaries = await player_summaries(session, players)
    await usage.log_event("export", {"format": "xlsx", "rows": len(summaries)}, user_id)
    return Response(
        exporting.players_xlsx(summaries),
        media_type=XLSX_MIME,
        headers={"Content-Disposition": "attachment; filename=players.xlsx"},
    )


async def _detail_or_404(session: AsyncSession, player_id: int) -> dict:
    player = await session.get(Player, player_id)
    if player is None:
        raise HTTPException(404, "player not found")
    return await player_detail(session, player)


@router.get("/export/players/{player_id}.pdf")
async def export_profile_pdf(
    player_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> Response:
    detail = await _detail_or_404(session, player_id)
    pdf = exporting.html_to_pdf(exporting.profile_html(detail))
    await usage.log_event("export", {"format": "pdf", "player_id": player_id}, user_id)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=player-{player_id}.pdf"},
    )


@router.get("/export/compare.pdf")
async def export_compare_pdf(
    a: int,
    b: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Header("demo-user", alias="X-User-Id"),
) -> Response:
    player_a = await session.get(Player, a)
    player_b = await session.get(Player, b)
    if player_a is None or player_b is None:
        raise HTTPException(404, "player not found")
    detail_a = await player_detail(session, player_a)
    detail_b = await player_detail(session, player_b)
    pair = await similarity.pair_similarity(session, player_a, player_b)
    pdf = exporting.html_to_pdf(exporting.compare_html(detail_a, detail_b, pair))
    await usage.log_event("export", {"format": "pdf", "compare": [a, b]}, user_id)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=compare-{a}-{b}.pdf"},
    )
