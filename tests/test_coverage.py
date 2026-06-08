"""Tests for placeholder detection and coverage computation."""

import math

from inventory_gap_analyzer.coverage import compute_coverage, is_placeholder
from inventory_gap_analyzer.ingest import load_workbooks


def test_is_placeholder():
    ph = ["", "N/A", "TBD", "Unknown", "-"]
    assert is_placeholder("", ph)
    assert is_placeholder("n/a", ph)  # case-insensitive
    assert is_placeholder("  TBD  ", ph)  # stripped
    assert is_placeholder(None, ph)
    assert is_placeholder(float("nan"), ph)
    assert not is_placeholder("Alpha", ph)
    assert not is_placeholder(0, ph)


def test_compute_coverage_population_rate(input_dir, schema_fields, placeholders):
    wbs = {w.filename: w for w in load_workbooks(input_dir)}
    wb = wbs["ParkService_Application_Inventory.xlsx"]
    mappings = {
        wb.filename: {
            "Application Name": "application_name",
            "Description": "description",
            "ATO Status": "ato_status",
        }
    }
    res = compute_coverage(wb, mappings, schema_fields, placeholders)
    assert res.total_records == 3

    # application_name: all 3 populated.
    assert math.isclose(res.field_coverage["application_name"].population_rate, 1.0)
    # description: one is "N/A" placeholder -> 2/3.
    assert math.isclose(res.field_coverage["description"].population_rate, 2 / 3)
    # ato_status: one is "" -> 2/3.
    assert math.isclose(res.field_coverage["ato_status"].population_rate, 2 / 3)


def test_structural_gaps_and_unmapped(input_dir, schema_fields, placeholders):
    wbs = {w.filename: w for w in load_workbooks(input_dir)}
    wb = wbs["ParkService_Application_Inventory.xlsx"]
    mappings = {wb.filename: {"Application Name": "application_name"}}
    res = compute_coverage(wb, mappings, schema_fields, placeholders)

    # Required-but-unmapped fields are structural gaps (e.g. bureau, description).
    assert "bureau" in res.structural_gaps
    assert "application_name" not in res.structural_gaps
    # Unmapped source columns should include the columns we didn't map.
    assert "Description" in res.unmapped_source_columns
    assert "Application Name" not in res.unmapped_source_columns


def test_sparse_field_detection(input_dir, schema_fields, placeholders):
    wbs = {w.filename: w for w in load_workbooks(input_dir)}
    wb = wbs["ParkService_Application_Inventory.xlsx"]
    mappings = {wb.filename: {"ATO Status": "ato_status"}}
    # threshold 0.9 -> ato_status (2/3) is sparse.
    res = compute_coverage(wb, mappings, schema_fields, placeholders, sparse_threshold=0.9)
    assert "ato_status" in res.sparse_fields
