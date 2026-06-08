"""Self-contained HTML dashboard generator."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .coverage import CoverageResult

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _build_payload(results: list[CoverageResult]) -> dict:
    bureaus = []
    field_names: list[str] = []
    for res in sorted(results, key=lambda r: r.bureau):
        if not field_names:
            field_names = list(res.field_coverage.keys())
        fields = []
        for name, fc in res.field_coverage.items():
            fields.append(
                {
                    "canonical": name,
                    "mapped": fc.mapped,
                    "source_column": fc.source_column,
                    "populated": fc.populated,
                    "total": fc.total,
                    "rate": round(fc.population_rate, 4),
                    "distinct": fc.distinct_values,
                    "required": fc.required,
                    "structural_gap": name in res.structural_gaps,
                    "sparse": name in res.sparse_fields,
                }
            )
        bureaus.append(
            {
                "bureau": res.bureau,
                "filename": res.filename,
                "sheet_name": res.sheet_name,
                "total_records": res.total_records,
                "fields": fields,
                "structural_gaps": res.structural_gaps,
                "sparse_fields": res.sparse_fields,
                "unmapped_source_columns": res.unmapped_source_columns,
            }
        )
    return {"bureaus": bureaus, "field_names": field_names}


def generate_dashboard(results: list[CoverageResult], output_dir: str | Path) -> Path:
    """Render the dashboard template to output/dashboard.html."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("dashboard.html.j2")
    payload = _build_payload(results)
    html = template.render(data_json=json.dumps(payload))
    path = out / "dashboard.html"
    path.write_text(html, encoding="utf-8")
    return path
