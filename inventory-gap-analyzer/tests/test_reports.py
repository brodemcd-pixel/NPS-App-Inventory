"""Tests for report and dashboard writers."""

import pandas as pd

from inventory_gap_analyzer.coverage import compute_coverage
from inventory_gap_analyzer.dashboard import generate_dashboard
from inventory_gap_analyzer.ingest import load_workbooks
from inventory_gap_analyzer.reports import (
    write_bureau_reports,
    write_coverage_matrix,
    write_record_gaps,
    write_run_log,
)


def _results(input_dir, schema_fields, placeholders):
    mappings = {
        "ParkService_Application_Inventory.xlsx": {
            "Application Name": "application_name",
            "Description": "description",
            "Owner": "application_owner",
            "Bureau": "bureau",
        }
    }
    out = []
    for wb in load_workbooks(input_dir):
        out.append(compute_coverage(wb, mappings, schema_fields, placeholders))
    return out


def test_coverage_matrix_csv(tmp_path, input_dir, schema_fields, placeholders):
    results = _results(input_dir, schema_fields, placeholders)
    write_coverage_matrix(results, tmp_path)
    csv_path = tmp_path / "coverage_matrix.csv"
    assert csv_path.exists()
    assert (tmp_path / "coverage_matrix.xlsx").exists()
    df = pd.read_csv(csv_path)
    assert "bureau" in df.columns
    assert "application_name" in df.columns
    assert len(df) == len(results)


def test_record_gaps_csv(tmp_path, input_dir, schema_fields, placeholders):
    results = _results(input_dir, schema_fields, placeholders)
    write_record_gaps(results, tmp_path)
    df = pd.read_csv(tmp_path / "record_gaps.csv")
    assert {"bureau", "canonical_field", "population_rate", "structural_gap"} <= set(df.columns)
    # One row per (bureau, field).
    assert len(df) == len(results) * len(schema_fields)


def test_bureau_reports_markdown(tmp_path, input_dir, schema_fields, placeholders):
    results = _results(input_dir, schema_fields, placeholders)
    paths = write_bureau_reports(results, tmp_path)
    assert paths
    text = paths[0].read_text()
    assert text.startswith("# ")
    assert "## Field Coverage" in text
    assert "## Structural Gaps" in text


def test_run_log(tmp_path):
    p = write_run_log(["line one", "line two"], tmp_path)
    assert p.read_text().splitlines() == ["line one", "line two"]


def test_dashboard_self_contained(tmp_path, input_dir, schema_fields, placeholders):
    results = _results(input_dir, schema_fields, placeholders)
    p = generate_dashboard(results, tmp_path)
    html = p.read_text()
    assert "<html" in html
    # No external network calls.
    assert "http://" not in html and "https://" not in html
    assert "createObjectURL" in html
