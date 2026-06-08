"""Column-to-canonical mapping via fuzzy matching."""

from __future__ import annotations

from pathlib import Path

import yaml
from rapidfuzz import fuzz

from . import load_yaml

# Confidence thresholds (rapidfuzz ratio 0-100).
HIGH = 85.0
MEDIUM = 65.0
LOW = 50.0


def confidence_label(score: float) -> str:
    if score > HIGH:
        return "high"
    if score > MEDIUM:
        return "medium"
    if score > LOW:
        return "low"
    return "unmapped"


def _normalize(text: str) -> str:
    return str(text).strip().lower().replace("_", " ").replace("-", " ")


def _best_field_match(column: str, schema_fields: list[dict]) -> tuple[str | None, float]:
    """Return (field_name, score) for the best canonical match of a source column."""
    col_norm = _normalize(column)
    best_field = None
    best_score = 0.0
    for fld in schema_fields:
        candidates = [fld["name"], _normalize(fld["name"])]
        candidates += [_normalize(s) for s in fld.get("synonyms", [])]
        field_best = max(
            (fuzz.token_sort_ratio(col_norm, _normalize(c)) for c in candidates),
            default=0.0,
        )
        if field_best > best_score:
            best_score = field_best
            best_field = fld["name"]
    return best_field, best_score


def suggest_mappings(
    workbooks: list,
    schema_fields: list[dict],
    config_dir: str | Path,
) -> dict:
    """Suggest column->canonical mappings per workbook; write suggested yaml.

    Returns the suggestions dict that was written.
    """
    config_dir = Path(config_dir)
    suggestions: dict[str, dict] = {}

    for wb in sorted(workbooks, key=lambda w: w.filename):
        per_file: dict[str, dict] = {}
        for column in sorted(str(c) for c in wb.df.columns):
            field_name, score = _best_field_match(column, schema_fields)
            label = confidence_label(score)
            per_file[column] = {
                "canonical": field_name if label != "unmapped" else None,
                "score": round(float(score), 1),
                "confidence": label,
            }
        suggestions[wb.filename] = per_file

    out_path = config_dir / "column_mappings.suggested.yaml"
    header = (
        "# AUTO-GENERATED suggestions. Review and promote approved entries\n"
        "# into config/column_mappings.yaml under the 'mappings' key.\n"
    )
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(header)
        yaml.safe_dump(
            {"mappings": suggestions}, fh, sort_keys=True, default_flow_style=False
        )
    return suggestions


def load_mappings(config_dir: str | Path, use_suggested: bool = False) -> dict:
    """Load approved (or suggested) column mappings.

    Returns: { filename: { source_column: canonical_field_or_None } }
    Suggested entries are normalized from the richer suggestion format.
    """
    config_dir = Path(config_dir)
    filename = (
        "column_mappings.suggested.yaml" if use_suggested else "column_mappings.yaml"
    )
    data = load_yaml(config_dir / filename)
    raw = data.get("mappings", {}) or {}

    normalized: dict[str, dict] = {}
    for fname, cols in raw.items():
        normalized[fname] = {}
        for col, target in (cols or {}).items():
            if isinstance(target, dict):
                normalized[fname][col] = target.get("canonical")
            else:
                normalized[fname][col] = target
    return normalized
