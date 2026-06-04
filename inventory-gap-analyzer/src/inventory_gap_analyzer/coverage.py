"""Coverage computation per workbook."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class FieldCoverage:
    canonical: str
    mapped: bool
    source_column: str | None
    populated: int
    total: int
    population_rate: float
    distinct_values: int
    required: bool
    null_ok: bool
    researchable: bool


@dataclass
class CoverageResult:
    bureau: str
    filename: str
    sheet_name: str
    total_records: int
    field_coverage: dict[str, FieldCoverage] = field(default_factory=dict)
    structural_gaps: list[str] = field(default_factory=list)  # required canonical, unmapped
    sparse_fields: list[str] = field(default_factory=list)  # mapped but below threshold
    unmapped_source_columns: list[str] = field(default_factory=list)


def is_placeholder(value, placeholders: list[str]) -> bool:
    """True if value is null-equivalent (NaN or a placeholder string, case-insensitive)."""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (ValueError, TypeError):
        pass
    norm = str(value).strip().lower()
    placeholder_set = {str(p).strip().lower() for p in placeholders}
    return norm in placeholder_set


def compute_coverage(
    workbook,
    mappings: dict,
    schema_fields: list[dict],
    placeholders: list[str],
    sparse_threshold: float = 0.5,
) -> CoverageResult:
    """Compute coverage for a single workbook against the canonical schema."""
    df = workbook.df
    total = len(df)
    file_map = mappings.get(workbook.filename, {})

    # canonical field -> source column (first mapped wins, sorted for determinism).
    canonical_to_source: dict[str, str] = {}
    for source_col in sorted(file_map.keys()):
        canonical = file_map[source_col]
        if canonical and canonical not in canonical_to_source:
            canonical_to_source[canonical] = source_col

    mapped_source_cols = {
        col for col, canon in file_map.items() if canon
    }
    unmapped_source = sorted(
        str(c) for c in df.columns if str(c) not in mapped_source_cols
    )

    result = CoverageResult(
        bureau=workbook.bureau,
        filename=workbook.filename,
        sheet_name=workbook.sheet_name,
        total_records=total,
        unmapped_source_columns=unmapped_source,
    )

    for fld in schema_fields:
        name = fld["name"]
        source = canonical_to_source.get(name)
        mapped = source is not None and source in df.columns

        if mapped:
            series = df[source]
            non_placeholder = series.apply(lambda v: not is_placeholder(v, placeholders))
            populated = int(non_placeholder.sum())
            distinct = int(series[non_placeholder].astype(str).str.strip().nunique())
        else:
            populated = 0
            distinct = 0

        rate = (populated / total) if total else 0.0

        fc = FieldCoverage(
            canonical=name,
            mapped=mapped,
            source_column=source if mapped else None,
            populated=populated,
            total=total,
            population_rate=rate,
            distinct_values=distinct,
            required=bool(fld.get("required", False)),
            null_ok=bool(fld.get("null_ok", True)),
            researchable=bool(fld.get("researchable", False)),
        )
        result.field_coverage[name] = fc

        if fld.get("required") and not mapped:
            result.structural_gaps.append(name)
        if mapped and rate < sparse_threshold:
            result.sparse_fields.append(name)

    result.structural_gaps.sort()
    result.sparse_fields.sort()
    return result
