"""Tests for workbook discovery and sheet selection."""

from inventory_gap_analyzer.ingest import derive_bureau, load_workbooks


def test_derive_bureau_strips_suffixes():
    assert derive_bureau("ParkService_Application_Inventory.xlsx") == "ParkService"
    assert derive_bureau("RangerCorps_Systems_List.xlsx") == "RangerCorps"
    assert derive_bureau("BLM_Application_Hosting_Inventory.xlsx") == "BLM"


def test_load_workbooks_discovers_all(input_dir):
    wbs = load_workbooks(input_dir)
    assert len(wbs) == 2
    names = sorted(w.filename for w in wbs)
    assert names == [
        "ParkService_Application_Inventory.xlsx",
        "RangerCorps_Systems_List.xlsx",
    ]


def test_single_sheet_selection_logged(input_dir):
    wbs = {w.filename: w for w in load_workbooks(input_dir)}
    wb = wbs["ParkService_Application_Inventory.xlsx"]
    assert wb.total_records == 3
    assert any("single sheet" in line for line in wb.log)


def test_multi_sheet_heuristic_picks_data_sheet(input_dir):
    wbs = {w.filename: w for w in load_workbooks(input_dir)}
    wb = wbs["RangerCorps_Systems_List.xlsx"]
    # Heuristic must pick the 'Systems' sheet (app-name column + more data),
    # not the first 'Instructions' sheet.
    assert wb.sheet_name == "Systems"
    assert wb.total_records == 2
    assert any("heuristic selected 'Systems'" in line for line in wb.log)


def test_sheet_selection_override(input_dir):
    override = {"RangerCorps_Systems_List.xlsx": "Instructions"}
    wbs = {w.filename: w for w in load_workbooks(input_dir, sheet_selection=override)}
    wb = wbs["RangerCorps_Systems_List.xlsx"]
    assert wb.sheet_name == "Instructions"
    assert any("sheet override" in line for line in wb.log)


def test_include_exclude(input_dir):
    only = load_workbooks(input_dir, include=["ParkService_Application_Inventory.xlsx"])
    assert len(only) == 1
    excl = load_workbooks(input_dir, exclude=["ParkService_Application_Inventory.xlsx"])
    assert len(excl) == 1
    assert excl[0].filename == "RangerCorps_Systems_List.xlsx"
