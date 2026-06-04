"""Tests for fuzzy column mapping and confidence scoring."""

from inventory_gap_analyzer.ingest import load_workbooks
from inventory_gap_analyzer.mapping import (
    _best_field_match,
    confidence_label,
    load_mappings,
    suggest_mappings,
)


def test_confidence_labels():
    assert confidence_label(90) == "high"
    assert confidence_label(70) == "medium"
    assert confidence_label(55) == "low"
    assert confidence_label(20) == "unmapped"


def test_exact_synonym_matches_high(schema_fields):
    field, score = _best_field_match("App Owner", schema_fields)
    assert field == "application_owner"
    assert score > 85


def test_application_name_matches(schema_fields):
    field, _ = _best_field_match("Application Name", schema_fields)
    assert field == "application_name"


def test_suggest_mappings_writes_file(tmp_path, input_dir, schema_fields):
    # Copy schema into a temp config dir so suggestions write there.
    config = tmp_path / "config"
    config.mkdir()
    wbs = load_workbooks(input_dir)
    suggestions = suggest_mappings(wbs, schema_fields, config)
    assert (config / "column_mappings.suggested.yaml").exists()
    assert set(suggestions.keys()) == {w.filename for w in wbs}

    loaded = load_mappings(config, use_suggested=True)
    park = loaded["ParkService_Application_Inventory.xlsx"]
    # "Application Name" should map to application_name.
    assert park.get("Application Name") == "application_name"


def test_load_mappings_empty_when_missing(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    assert load_mappings(config) == {}
