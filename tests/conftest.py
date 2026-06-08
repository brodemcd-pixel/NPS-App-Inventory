"""Shared pytest fixtures: synthetic .xlsx workbooks and config."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from inventory_gap_analyzer import load_schema_fields, load_placeholders

REPO_CONFIG = Path(__file__).resolve().parents[1] / "config"


@pytest.fixture
def schema_fields() -> list[dict]:
    return load_schema_fields(REPO_CONFIG)


@pytest.fixture
def placeholders() -> list[str]:
    return load_placeholders(REPO_CONFIG)


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    """A directory with two synthetic workbooks (one single-sheet, one multi-sheet)."""
    d = tmp_path / "workbooks"
    d.mkdir()

    # Workbook 1: single sheet, clean column names.
    df1 = pd.DataFrame(
        {
            "Application Name": ["Alpha", "Beta", "Gamma"],
            "Description": ["a tool", "N/A", "another"],
            "Owner": ["Jo", "Sam", "Lee"],
            "Bureau": ["X", "X", "X"],
            "FISMA Level": ["Low", "Moderate", "TBD"],
            "ATO Status": ["Authorized", "", "Authorized"],
            "App Type": ["web", "web", "service"],
            "Public": ["yes", "no", "yes"],
            "Hosting": ["cloud", "on-prem", "cloud"],
        }
    )
    df1.to_excel(d / "ParkService_Application_Inventory.xlsx", index=False)

    # Workbook 2: multiple sheets; the data sheet is NOT first.
    path2 = d / "RangerCorps_Systems_List.xlsx"
    with pd.ExcelWriter(path2, engine="xlsxwriter") as xw:
        pd.DataFrame({"note": ["readme only"]}).to_excel(xw, sheet_name="Instructions", index=False)
        pd.DataFrame(
            {
                "System Name": ["Sys1", "Sys2"],
                "Summary": ["does things", "does more"],
                "App Owner": ["Pat", "Kim"],
                "Organization": ["Y", "Y"],
                "Security Level": ["High", "Low"],
                "Authorization Status": ["Authorized", "In Process"],
                "Category": ["web", "db"],
                "Internet Facing": ["yes", "no"],
                "Deployment Type": ["cloud", "cloud"],
            }
        ).to_excel(xw, sheet_name="Systems", index=False)

    return d
