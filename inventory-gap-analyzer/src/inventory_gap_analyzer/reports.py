"""CSV / Excel / Markdown report writers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .coverage import CoverageResult


def _ensure_dir(output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_coverage_matrix(results: list[CoverageResult], output_dir: str | Path) -> Path:
    """Write coverage_matrix.csv and .xlsx (bureaus x canonical fields, population rate)."""
    out = _ensure_dir(output_dir)
    rows = []
    for res in sorted(results, key=lambda r: r.bureau):
        row = {"bureau": res.bureau, "filename": res.filename, "total_records": res.total_records}
        for name, fc in res.field_coverage.items():
            row[name] = round(fc.population_rate, 4)
        rows.append(row)
    df = pd.DataFrame(rows)

    csv_path = out / "coverage_matrix.csv"
    df.to_csv(csv_path, index=False)

    xlsx_path = out / "coverage_matrix.xlsx"
    try:
        df.to_excel(xlsx_path, index=False, engine="xlsxwriter")
    except Exception:  # noqa: BLE001
        df.to_excel(xlsx_path, index=False)
    return csv_path


def write_record_gaps(results: list[CoverageResult], output_dir: str | Path) -> Path:
    """Write record_gaps.csv: one row per (bureau, field) with population stats."""
    out = _ensure_dir(output_dir)
    rows = []
    for res in sorted(results, key=lambda r: r.bureau):
        for name, fc in res.field_coverage.items():
            rows.append(
                {
                    "bureau": res.bureau,
                    "filename": res.filename,
                    "canonical_field": name,
                    "mapped": fc.mapped,
                    "source_column": fc.source_column or "",
                    "required": fc.required,
                    "populated": fc.populated,
                    "total_records": fc.total,
                    "missing": fc.total - fc.populated,
                    "population_rate": round(fc.population_rate, 4),
                    "distinct_values": fc.distinct_values,
                    "structural_gap": name in res.structural_gaps,
                    "sparse": name in res.sparse_fields,
                }
            )
    df = pd.DataFrame(rows)
    path = out / "record_gaps.csv"
    df.to_csv(path, index=False)
    return path


def write_bureau_reports(results: list[CoverageResult], output_dir: str | Path) -> list[Path]:
    """Write one markdown report per bureau."""
    out = _ensure_dir(output_dir)
    bureau_dir = out / "bureaus"
    bureau_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for res in sorted(results, key=lambda r: r.bureau):
        lines = [
            f"# {res.bureau} — Inventory Coverage Report",
            "",
            f"- **Source file:** `{res.filename}`",
            f"- **Sheet:** `{res.sheet_name}`",
            f"- **Total records:** {res.total_records}",
            "",
            "## Field Coverage",
            "",
            "| Canonical field | Mapped | Source column | Populated | Rate | Distinct |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for name, fc in res.field_coverage.items():
            lines.append(
                f"| {name} | {'yes' if fc.mapped else 'no'} | "
                f"{fc.source_column or '—'} | {fc.populated}/{fc.total} | "
                f"{fc.population_rate:.0%} | {fc.distinct_values} |"
            )

        lines += ["", "## Structural Gaps (required, unmapped)", ""]
        if res.structural_gaps:
            lines += [f"- {g}" for g in res.structural_gaps]
        else:
            lines.append("_None_")

        lines += ["", "## Sparse Fields (mapped, below threshold)", ""]
        if res.sparse_fields:
            for s in res.sparse_fields:
                fc = res.field_coverage[s]
                lines.append(f"- {s} ({fc.population_rate:.0%})")
        else:
            lines.append("_None_")

        lines += ["", "## Unmapped Source Columns", ""]
        if res.unmapped_source_columns:
            lines += [f"- {c}" for c in res.unmapped_source_columns]
        else:
            lines.append("_None_")
        lines.append("")

        safe = res.bureau.replace("/", "_").replace(" ", "_")
        path = bureau_dir / f"{safe}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        paths.append(path)
    return paths


def write_run_log(log_entries: list[str], output_dir: str | Path) -> Path:
    """Write run.log with all decision/log entries."""
    out = _ensure_dir(output_dir)
    path = out / "run.log"
    path.write_text("\n".join(log_entries) + "\n", encoding="utf-8")
    return path
