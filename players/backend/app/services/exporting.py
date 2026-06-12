"""Export generation (CONTRACT.md §6): XLSX via openpyxl, PDF via WeasyPrint.

WeasyPrint is an optional dependency with system-library requirements; when it is not
installed the PDF endpoints raise 501 and the frontend surfaces the message. XLSX export
has no optional dependencies and always works.
"""

from __future__ import annotations

import html
import io
from datetime import datetime, timezone

from fastapi import HTTPException
from openpyxl import Workbook

XLSX_COLUMNS = [
    ("Name", "name"), ("Class", "draft_class"), ("Pos", "position"),
    ("Group", "position_group"), ("College", "college"), ("Conf", "conference"),
    ("Height (in)", "height_in"), ("Weight (lb)", "weight_lb"), ("40yd", "forty"),
    ("Grade", "nfl_grade"), ("NGS", "ngs_athleticism"), ("Class %ile", "class_percentile"),
    ("Round", "draft_round"), ("Pick", "draft_pick"), ("Team", "draft_team"),
    ("Scheme", "scheme_archetype"), ("Tree", "coaching_tree"),
    ("Roles", "roles"), ("Red flag", "red_flag"), ("Green flag", "green_flag"),
]


def players_xlsx(summaries: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Prospects"
    ws.append([label for label, _ in XLSX_COLUMNS])
    for row in summaries:
        ws.append([
            ", ".join(row[key]) if key == "roles" else row.get(key)
            for _, key in XLSX_COLUMNS
        ])
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF (optional WeasyPrint)

_CSS = """
body { font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #1a202c; }
h1 { font-size: 20px; margin-bottom: 0; } h2 { font-size: 13px; margin: 14px 0 4px;
border-bottom: 1px solid #cbd5e0; } .muted { color: #718096; }
table { border-collapse: collapse; width: 100%; margin-top: 4px; }
td, th { border: 1px solid #e2e8f0; padding: 3px 6px; text-align: left; }
.cols { display: flex; gap: 16px; } .col { flex: 1; }
.flag-red { color: #c53030; } .flag-green { color: #2f855a; }
"""


def _esc(value) -> str:
    return html.escape(str(value)) if value is not None else "—"


def _measurables_rows(m: dict) -> str:
    labels = [
        ("Height (in)", "height_in"), ("Weight (lb)", "weight_lb"), ("40-yard", "forty"),
        ("Vertical (in)", "vertical_in"), ("Broad (in)", "broad_in"),
        ("3-cone", "three_cone"), ("Shuttle", "shuttle"), ("Bench", "bench_reps"),
        ("Arm (in)", "arm_length_in"), ("Hand (in)", "hand_size_in"),
        ("Wingspan (in)", "wingspan_in"),
    ]
    return "".join(
        f"<tr><th>{label}</th><td>{_esc(m.get(key))}</td></tr>" for label, key in labels
    )


def _profile_body(d: dict) -> str:
    draft = (f"Round {d['draft_round']}, pick {d['draft_pick']} — {_esc(d['draft_team'])}"
             if d.get("draft_pick") else "Undrafted / draft-eligible")
    flags = ""
    if d["flags"]["red_flag"]:
        flags = f"<p class='flag-red'>RED FLAG: {_esc(d['flags']['notes'])}</p>"
    elif d["flags"]["green_flag"]:
        flags = f"<p class='flag-green'>GREEN FLAG: {_esc(d['flags']['notes'])}</p>"
    mental = "".join(
        f"<tr><td>{_esc(t['trait'])}</td><td>{t['score']:.2f}</td>"
        f"<td>{', '.join(t['sources'])}</td></tr>"
        for t in d["mental_profile"]["core"]
    )
    schemes = "".join(
        f"<tr><td>{s['season']}</td><td>{_esc(s['scheme_archetype'])}</td>"
        f"<td>{_esc(s['coordinator'])}</td><td>{_esc(s['coaching_tree'])}</td></tr>"
        for s in d["scheme_context"]
    )
    return f"""
    <h1>{_esc(d['name'])}</h1>
    <p class="muted">{_esc(d['position'])} · {_esc(d['college'])} ·
      class of {d['draft_class']} · grade {d['nfl_grade']} · {draft}</p>
    {flags}
    <div class="cols"><div class="col">
      <h2>Measurables (measurement)</h2><table>{_measurables_rows(d['measurables'])}</table>
    </div><div class="col">
      <h2>Mental profile (directional signal)</h2>
      <table><tr><th>Trait</th><th>Score</th><th>Sources</th></tr>{mental}</table>
      <h2>Scheme context</h2>
      <table><tr><th>Season</th><th>Scheme</th><th>Coordinator</th><th>Tree</th></tr>
      {schemes}</table>
    </div></div>
    <h2>Overview (opinion)</h2><p>{_esc(d['report']['overview'])}</p>
    <h2>Strengths (opinion)</h2><p>{_esc(d['report']['strengths'])}</p>
    <h2>Weaknesses (opinion)</h2><p>{_esc(d['report']['weaknesses'])}</p>
    <h2>Sources tell us</h2><p>{_esc(d['report']['sources_tell_us'])}</p>
    """


def _document(title: str, body: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<html><head><meta charset="utf-8"><style>{_CSS}</style></head>
    <body>{body}<p class="muted">Players — generated {stamp}. Synthetic demo data;
    opinion (scouting language) and measurement are labeled.</p></body></html>"""


def profile_html(detail: dict) -> str:
    return _document(detail["name"], _profile_body(detail))


def compare_html(a: dict, b: dict, similarity: dict) -> str:
    axes = ", ".join(
        f"{k}: {v:.2f}" for k, v in similarity["axes"].items() if v is not None
    )
    header = f"""
    <h1>Compare: {_esc(a['name'])} vs {_esc(b['name'])}</h1>
    <p>FSM v1.0 similarity <b>{similarity['overall']:.3f}</b> ({axes})</p>
    """
    body = (header + '<div class="cols"><div class="col">' + _profile_body(a)
            + '</div><div class="col">' + _profile_body(b) + "</div></div>")
    return _document("Compare", body)


def html_to_pdf(document: str) -> bytes:
    try:
        from weasyprint import HTML  # type: ignore
    except Exception as exc:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires WeasyPrint "
                   "(pip install -r requirements-optional.txt)",
        ) from exc
    return HTML(string=document).write_pdf()
