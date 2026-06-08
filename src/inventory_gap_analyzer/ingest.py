"""Workbook & sheet loading with explicit, logged sheet selection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Common suffixes stripped from filename stems when deriving a bureau name.
_BUREAU_SUFFIXES = [
    "_application_hosting_inventory",
    "_application_inventory",
    "_app_inventory",
    "_systems_list",
    "_system_list",
    "_systems_inventory",
    "_inventory",
    "_applications",
    "_apps",
    "_list",
]

# Tokens that hint a column holds an application/system name.
_APP_NAME_HINTS = ["application name", "app name", "system name", "application", "name"]


@dataclass
class WorkbookData:
    """A single loaded workbook + chosen sheet."""

    filename: str
    bureau: str
    sheet_name: str
    df: pd.DataFrame
    total_records: int
    log: list[str] = field(default_factory=list)


def derive_bureau(filename: str) -> str:
    """Derive a bureau name from a workbook filename."""
    stem = Path(filename).stem
    lowered = stem.lower()
    for suffix in _BUREAU_SUFFIXES:
        if lowered.endswith(suffix):
            stem = stem[: len(stem) - len(suffix)]
            break
    # First component (split on common separators), preserve original casing.
    parts = re.split(r"[ _\-]+", stem)
    parts = [p for p in parts if p]
    return parts[0] if parts else stem or filename


def _looks_like_app_name(col: str) -> bool:
    c = str(col).strip().lower()
    return any(hint in c for hint in _APP_NAME_HINTS)


def _score_sheet(df: pd.DataFrame) -> tuple[int, int, int]:
    """Score a sheet: (has_app_name_col, non_null_cells, n_rows)."""
    if df is None or df.empty:
        return (0, 0, 0)
    has_name = 1 if any(_looks_like_app_name(c) for c in df.columns) else 0
    non_null = int(df.notna().to_numpy().sum())
    return (has_name, non_null, len(df))


def select_sheet(
    filename: str,
    xls: pd.ExcelFile,
    sheet_selection: dict | None,
    log: list[str],
) -> str:
    """Choose a sheet, logging every decision. Never silently picks the first sheet."""
    sheet_selection = sheet_selection or {}
    basename = Path(filename).name
    sheets = list(xls.sheet_names)

    # 1. Explicit override.
    if basename in sheet_selection:
        chosen = sheet_selection[basename]
        if chosen in sheets:
            log.append(f"[{basename}] sheet override -> '{chosen}' (from sheet_selection.yaml)")
            return chosen
        log.append(
            f"[{basename}] override '{chosen}' not found in {sheets}; falling back to heuristic"
        )

    # 2. Single sheet: still log it.
    if len(sheets) == 1:
        log.append(f"[{basename}] single sheet -> '{sheets[0]}'")
        return sheets[0]

    # 3. Heuristic: most app-name-like + most non-null + most rows.
    best_sheet = None
    best_score = (-1, -1, -1)
    for sheet in sorted(sheets):
        try:
            df = xls.parse(sheet)
        except Exception as exc:  # noqa: BLE001
            log.append(f"[{basename}] sheet '{sheet}' unreadable ({exc}); skipped")
            continue
        score = _score_sheet(df)
        log.append(
            f"[{basename}] candidate '{sheet}': app_name_col={score[0]} "
            f"non_null={score[1]} rows={score[2]}"
        )
        if score > best_score:
            best_score = score
            best_sheet = sheet

    if best_sheet is None:
        best_sheet = sorted(sheets)[0]
        log.append(f"[{basename}] no scorable sheet; defaulting to '{best_sheet}'")
    else:
        log.append(
            f"[{basename}] heuristic selected '{best_sheet}' "
            f"(app_name_col={best_score[0]}, non_null={best_score[1]}, rows={best_score[2]})"
        )
    return best_sheet


def load_workbooks(
    input_dir: str | Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    sheet_selection: dict | None = None,
) -> list[WorkbookData]:
    """Discover .xlsx files in input_dir and load the selected sheet from each."""
    input_dir = Path(input_dir)
    include = set(include) if include else None
    exclude = set(exclude) if exclude else set()

    files = sorted(
        p for p in input_dir.glob("*.xlsx") if not p.name.startswith("~$")
    )

    workbooks: list[WorkbookData] = []
    for path in files:
        name = path.name
        if include is not None and name not in include:
            continue
        if name in exclude:
            continue

        log: list[str] = []
        with pd.ExcelFile(path) as xls:
            sheet = select_sheet(name, xls, sheet_selection, log)
            df = xls.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]

        workbooks.append(
            WorkbookData(
                filename=name,
                bureau=derive_bureau(name),
                sheet_name=sheet,
                df=df,
                total_records=len(df),
                log=log,
            )
        )
    return workbooks
