"""AI assistant orchestration (CONTRACT.md §6 chat, §7 operations).

Two engines behind one streaming interface:

- Live: Anthropic Claude with the 12-tool registry, agentic loop while stop_reason is
  "tool_use", token deltas streamed as they arrive.
- Offline (no ANTHROPIC_API_KEY): a rule-based intent router that executes the same
  tools directly and formats a plain-text answer, emitting the identical event sequence
  so the product is fully demoable without a key.

Both yield ("tool"|"text"|"sources"|"done"|"error", payload) tuples; the chat router
frames them as SSE events. A Sources block is assembled from the tool calls that
actually ran — similarity scores only ever come from FSM tool output, and the system
prompt requires opinion (scouting language) to be labeled separately from measurement.
"""

from __future__ import annotations

import json
import re
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.domain import ALL_ROLES, DEFENSE_SCHEMES, OFFENSE_SCHEMES
from backend.app.tools.registry import TOOLS, run_tool
from ml.mental_traits import CORE_TRAITS

MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """You are the Players assistant, a research tool for NFL draft scouts \
covering the 2022–2026 draft classes. You answer ONLY using the provided tools — never \
from memory. The dataset in this deployment is synthetic demo data with fictional players.

Rulebook (non-negotiable):
1. Every factual claim must come from a tool result in this conversation.
2. Similarity scores may only be cited when they come from the similarity_comparison or \
player_compare tools (the FSM model). Never estimate similarity yourself.
3. Label opinion separately from measurement: scouting-report language is opinion; \
combine numbers, production stats and draft outcomes are measurement. Mental trait \
scores are directional NLP signals, not measurements — say so when you cite them.
4. When a tool returns player ids, link players as [Name](/players/{id}).
5. Be concise and scout-like: lead with the answer, then the supporting numbers.
6. A Sources block listing your exact lookups is appended automatically — do not write \
your own sources section.
"""

Event = tuple[str, dict]


def _source_entry(name: str, result: dict) -> dict:
    return {
        "operation": name,
        "detail": result.get("detail", name),
        "count": result.get("count", 0),
    }


async def stream_chat(
    session: AsyncSession,
    message: str,
    history: list[dict] | None = None,
    weights: dict | None = None,
    user_id: str = "demo-user",
) -> AsyncIterator[Event]:
    try:
        if settings.anthropic_api_key:
            engine = _stream_live(session, message, history or [], weights, user_id)
        else:
            engine = _stream_offline(session, message, weights, user_id)
        async for event in engine:
            yield event
    except Exception as exc:
        yield ("error", {"detail": f"{type(exc).__name__}: {exc}"})


# ---------------------------------------------------------------------------
# Live engine (Anthropic)


async def _stream_live(
    session: AsyncSession,
    message: str,
    history: list[dict],
    weights: dict | None,
    user_id: str,
) -> AsyncIterator[Event]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    user_msg = message
    if weights:
        user_msg += f"\n\n[user-configured FSM weights: {json.dumps(weights)}]"
    messages: list[dict] = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and m.get("content")
    ] + [{"role": "user", "content": user_msg}]

    sources: list[dict] = []
    for _round in range(MAX_TOOL_ROUNDS):
        tool_calls: list[dict] = []
        async with client.messages.stream(
            model=settings.anthropic_model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    yield ("text", {"delta": event.delta.text})
            final = await stream.get_final_message()

        for block in final.content:
            if block.type == "tool_use":
                tool_calls.append(
                    {"id": block.id, "name": block.name, "input": block.input}
                )

        if final.stop_reason != "tool_use" or not tool_calls:
            break

        messages.append({"role": "assistant", "content": final.content})
        results = []
        for call in tool_calls:
            yield ("tool", {"name": call["name"], "input": call["input"]})
            result = await run_tool(session, call["name"], call["input"], user_id=user_id)
            sources.append(_source_entry(call["name"], result))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": json.dumps(result, default=str)[:20000],
                }
            )
        messages.append({"role": "user", "content": results})

    yield ("sources", {"sources": sources})
    yield ("done", {})


# ---------------------------------------------------------------------------
# Offline engine (rule-based router over the same tools)

_SCHEMES = OFFENSE_SCHEMES + DEFENSE_SCHEMES
_TRAIT_WORDS = {t.replace("_", " "): t for t in CORE_TRAITS}

_COMPARE_RE = re.compile(
    r"\bcompare\s+(.+?)\s+(?:and|vs\.?|versus|to|with)\s+(.+?)\s*$", re.I)
_SIMILAR_RE = re.compile(
    r"\b(?:similar(?:\s+players?)?\s+to|comps?\s+for|comparable\s+to)\s+(.+?)\s*$", re.I)
_TEAMFIT_RE = re.compile(
    r"\b(?:team\s+fits?|which\s+teams?\s+fit|best\s+teams?)\s*(?:for)?\s+(.+?)\s*$", re.I)
_PRODUCTION_RE = re.compile(
    r"\b(?:production|college\s+stats?|stat\s+line)\s*(?:for|of)?\s+(.+?)\s*$", re.I)
_NFL_RE = re.compile(
    r"\b(?:nfl\s+(?:outcome|production|stats?|career)|how\s+has)\s+(.+?)(?:\s+done.*)?\s*$",
    re.I)
_PROFILE_RE = re.compile(
    r"\b(?:profile\s*(?:for|of)?|who\s+is|tell\s+me\s+about|look\s*up)\s+(.+?)\s*\??\s*$",
    re.I)
_COMMENT_RE = re.compile(r"\b(?:note|comment)\s+on\s+(.+?)\s*[:\-]\s*(.+)$", re.I)
_FASTEST_RE = re.compile(r"\b(\d{1,2})?\s*fastest\b", re.I)
_FORTY_UNDER_RE = re.compile(r"\bunder\s+(4\.\d{1,2})\b", re.I)
_LIMIT_RE = re.compile(r"\b(?:top|first)\s+(\d{1,2})\b", re.I)

_POS_WORDS = {
    "quarterback": "QB", "qb": "QB", "running back": "RB", "rb": "RB",
    "receiver": "WR", "wr": "WR", "tight end": "TE", "te": "TE",
    "tackle": "OT", "ot": "OT", "guard": "IOL", "center": "IOL", "iol": "IOL",
    "edge rusher": "EDGE", "edge": "EDGE", "defensive tackle": "DT", "dt": "DT",
    "linebacker": "LB", "lb": "LB", "cornerback": "CB", "corner": "CB", "cb": "CB",
    "safety": "S", "safeties": "S",
}


def _positions_in(text: str) -> list[str]:
    low = f" {text.lower()} "
    found = []
    for word, pos in _POS_WORDS.items():
        if f" {word}s " in low or f" {word} " in low:
            if pos not in found:
                found.append(pos)
    return found


def _classes_in(text: str) -> list[int]:
    return [int(y) for y in re.findall(r"\b(202[2-6])\b", text)]


def _strip_question(name: str) -> str:
    return re.sub(r"[\?\.\!]+$", "", name).strip()


def _route(message: str, weights: dict | None) -> tuple[str, dict] | None:
    """Map a message to (tool_name, args); None when no intent matches."""
    msg = message.strip()
    if m := _COMMENT_RE.search(msg):
        return "scout_comment", {"name_or_id": _strip_question(m.group(1)),
                                 "body": m.group(2).strip()}
    if m := _COMPARE_RE.search(msg):
        return "player_compare", {"a_name_or_id": _strip_question(m.group(1)),
                                  "b_name_or_id": _strip_question(m.group(2)),
                                  **({"weights": weights} if weights else {})}
    if m := _SIMILAR_RE.search(msg):
        return "similarity_comparison", {"name_or_id": _strip_question(m.group(1)),
                                         **({"weights": weights} if weights else {})}
    if m := _TEAMFIT_RE.search(msg):
        return "team_fit", {"name_or_id": _strip_question(m.group(1))}
    if "nfl" in msg.lower() and (m := _NFL_RE.search(msg)):
        return "nfl_outcome_lookup", {"name_or_id": _strip_question(m.group(1))}
    if m := _PRODUCTION_RE.search(msg):
        return "production_lookup", {"name_or_id": _strip_question(m.group(1))}

    for scheme in _SCHEMES:
        if scheme.lower() in msg.lower():
            args: dict = {"scheme_archetype": scheme}
            if pos := _positions_in(msg):
                args["position"] = pos
            return "scheme_fit", args
    for role in ALL_ROLES:
        if role.lower() in msg.lower():
            return "role_search", {"functional_role": role}
    for phrase, trait in _TRAIT_WORDS.items():
        if phrase in msg.lower():
            args = {"trait": trait}
            if pos := _positions_in(msg):
                args["position"] = pos
            return "mental_profile_query", args

    fastest = _FASTEST_RE.search(msg)
    forty_under = _FORTY_UNDER_RE.search(msg)
    if fastest or forty_under or "40" in msg:
        args = {"sort": "forty", "limit": int((fastest and fastest.group(1)) or 5)}
        if forty_under:
            args["forty_max"] = float(forty_under.group(1))
        if pos := _positions_in(msg):
            args["position"] = pos
        if classes := _classes_in(msg):
            args["draft_class"] = classes
        return "filtered_list", args

    if _positions_in(msg) or _classes_in(msg) or re.search(r"\bround\b", msg, re.I):
        args = {"limit": 10}
        if m := _LIMIT_RE.search(msg):
            args["limit"] = int(m.group(1))
        if pos := _positions_in(msg):
            args["position"] = pos
        if classes := _classes_in(msg):
            args["draft_class"] = classes
        if m := re.search(r"\b(?:round|rd)\s*(\d)\b", msg, re.I):
            args["round"] = [int(m.group(1))]
        return "filtered_list", args

    if m := _PROFILE_RE.search(msg):
        return "player_profile", {"name_or_id": _strip_question(m.group(1))}
    return None


def _player_line(p: dict, extra: str = "") -> str:
    draft = (f"R{p['draft_round']} pick {p['draft_pick']} ({p['draft_team']})"
             if p.get("draft_pick") else "undrafted/eligible")
    forty = f", 40: {p['forty']:.2f}" if p.get("forty") else ""
    return (f"[{p['name']}](/players/{p['id']}) — {p['position']}, {p['college']}, "
            f"class of {p['draft_class']}; grade {p['nfl_grade']:.2f}{forty}; {draft}{extra}")


def _format_offline(name: str, result: dict) -> str:
    if result.get("error"):
        return f"Sorry — {result['error']}."
    lines: list[str] = []
    if name == "filtered_list":
        lines.append(f"**{result['count']} players** (measurement data):")
        lines += [f"{i+1}. {_player_line(p)}" for i, p in enumerate(result["players"])]
    elif name == "player_profile":
        p = result
        lines.append(_player_line({**p, "id": p["id"]}))
        lines.append(f"\n**Scouting report (opinion)** — {p['report']['overview']}")
        lines.append(f"**Strengths:** {p['report']['strengths']}")
        lines.append(f"**Weaknesses:** {p['report']['weaknesses']}")
        if core := p.get("mental_profile", {}).get("core"):
            traits = ", ".join(f"{t['trait']} {t['score']:.2f}" for t in core[:5])
            lines.append(f"**Mental profile (directional NLP signal):** {traits}")
    elif name == "report_search":
        lines.append(f"**{result['count']} reports** mention it (opinion text):")
        lines += [f"- {_player_line(m)}\n  {m['snippet']}" for m in result["matches"]]
    elif name == "similarity_comparison":
        a = result["anchor"]
        w = result["weights_used"]
        lines.append(
            f"FSM v1.0 comps for [{a['name']}](/players/{a['id']}) "
            f"(weights scouting {w['scouting']:.2f} / scheme {w['scheme']:.2f} / "
            f"mental {w['mental']:.2f}):")
        for i, item in enumerate(result["items"]):
            axes = item["axes"]
            ax = ", ".join(f"{k} {v:.2f}" for k, v in axes.items() if v is not None)
            lines.append(f"{i+1}. {_player_line(item['player'])} — overall "
                         f"**{item['overall']:.3f}** ({ax})")
    elif name == "player_compare":
        a, b, s = result["a"], result["b"], result["similarity"]
        lines.append(f"{_player_line(a)}\nvs\n{_player_line(b)}")
        ax = ", ".join(f"{k} {v:.2f}" for k, v in s["axes"].items() if v is not None)
        lines.append(f"FSM similarity: **{s['overall']:.3f}** ({ax})")
        ma, mb = a["measurables"], b["measurables"]
        for label, key in [("Height", "height_in"), ("Weight", "weight_lb"),
                           ("40", "forty"), ("NGS", "ngs_athleticism")]:
            lines.append(f"- {label}: {ma.get(key)} vs {mb.get(key)} (measurement)")
    elif name == "scheme_fit":
        lines.append(f"Players from the **{'/'.join(result['scheme_family'])}** family:")
        lines += [f"{i+1}. {_player_line(p)} [{p['scheme_archetype']}]"
                  for i, p in enumerate(result["players"])]
    elif name == "role_search":
        lines.append(f"**{result['role']}** prospects:")
        lines += [f"{i+1}. {_player_line(p)}" for i, p in enumerate(result["players"])]
    elif name == "mental_profile_query":
        if "players" in result:
            lines.append(f"Top **{result['trait']}** scores (directional NLP signal, "
                         f"not a measurement):")
            lines += [f"{i+1}. {_player_line(p)} — {p['trait_score']:.2f}"
                      for i, p in enumerate(result["players"])]
        else:
            p = result["player"]
            lines.append(f"Mental profile for {_player_line(p)} (directional signal):")
            lines += [f"- {t['trait']}: {t['score']:.2f} ({t['source']})"
                      for t in result["traits"][:10]]
    elif name == "production_lookup":
        p = result["player"]
        lines.append(f"College production for {_player_line(p)} "
                     f"(measurement; SOS tier {result['sos_tier']}/5):")
        for season, stats in sorted(result["seasons"].items()):
            shown = {k: v for k, v in stats.items() if not k.endswith("_team_share_pct")}
            lines.append(f"- {season}: " + ", ".join(f"{k} {v:g}" for k, v in shown.items()))
        t = result["trajectory"]
        lines.append(f"Trajectory: {t['trend']}, consistency {t['consistency']:.2f}, "
                     f"breakout age {result['breakout_age']}")
    elif name == "nfl_outcome_lookup":
        p = result["player"]
        lines.append(f"NFL outcomes for {_player_line(p)} (measurement):")
        if not result["nfl_seasons"]:
            lines.append("- no NFL production data on file")
        lines += [f"- {o['season']}: {o['games']} games, {o['snaps']} snaps, "
                  f"PFF {o['pff_grade']}" for o in result["nfl_seasons"]]
    elif name == "team_fit":
        p = result["player"]
        lines.append(f"Best NFL scheme fits for {_player_line(p)}:")
        lines += [f"{i+1}. **{t['team']}** ({t['scheme_archetype']}, {t['coaching_tree']} "
                  f"tree) — fit {t['fit']:.2f}" for i, t in enumerate(result["teams"])]
    elif name == "scout_comment":
        lines.append(f"Saved your note on [{result['player']['name']}]"
                     f"(/players/{result['player']['id']}) "
                     f"({result['tags_recorded']} trait tags recorded).")
    else:
        lines.append(json.dumps(result, default=str)[:1500])
    return "\n".join(lines)


_CAPABILITIES = """I couldn't match that to one of my operations. I can:
- filter prospects ("5 fastest 40 times", "round 1 WRs in 2024")
- look up a profile ("tell me about <player>")
- search report text ("reports that mention 'contact balance'")
- find comps ("similar to <player>") or compare two players ("compare A and B")
- scheme/role queries ("Air Raid receivers", "press-man corner prospects")
- mental profiles ("best leadership among QBs")
- production / NFL outcomes / team fits ("production for <player>", "team fits for <player>")
- log notes ("note on <player>: great interview")"""


async def _stream_offline(
    session: AsyncSession, message: str, weights: dict | None, user_id: str
) -> AsyncIterator[Event]:
    routed = _route(message, weights)
    if routed is None:
        yield ("text", {"delta": _CAPABILITIES})
        yield ("sources", {"sources": []})
        yield ("done", {})
        return
    name, args = routed
    yield ("tool", {"name": name, "input": args})
    result = await run_tool(session, name, args, user_id=user_id)
    text = _format_offline(name, result)
    # Stream in chunks so the UI exercises its incremental rendering path.
    for i in range(0, len(text), 400):
        yield ("text", {"delta": text[i:i + 400]})
    yield ("sources", {"sources": [_source_entry(name, result)]})
    yield ("done", {})
