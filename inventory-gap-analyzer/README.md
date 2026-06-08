# inventory-gap-analyzer

> **TL;DR** — Drop your bureau Excel workbooks in a folder, run two commands, and get a full picture of what data is missing before you touch the extraction pipeline.

A Python CLI that measures **coverage and structural gaps** across bureau-submitted application-inventory workbooks, measured against the locked 21-field canonical schema used in the NPS / DOI application inventory migration.

It maps each workbook's columns to canonical fields, computes how well each field is populated per bureau, and emits five outputs: a coverage matrix, per-bureau Markdown reports, a per-record gap CSV (your outreach driver), a self-contained HTML dashboard, and a full audit log.

**This tool is analysis-only.** It never modifies source workbooks, never generates upload JSON, and never calls the network.

---

## What it does in plain English

You have 12 Excel workbooks submitted by different bureaus. Each one has different column names, different sheet layouts, and varying levels of completeness. Before you can extract records into the inventory system you need to know: *what's missing and where?*

This tool answers that in two steps:

1. **`suggest-mappings`** — looks at each workbook's column headers and fuzzy-matches them against the 21 canonical field names. Writes a suggested mapping file for you to review and correct. **Nothing is applied automatically.**

2. **`analyze`** — loads your approved mappings, processes all workbooks, and writes five output files telling you exactly which bureaus are missing which fields, down to the individual record level.

The outputs let you prioritize owner outreach *before* extraction, so that gap-filling and extraction run in parallel rather than in series.

---

## Installation

```bash
git clone <repo>
cd inventory-gap-analyzer
pip install -e .
```

Requires Python >= 3.11.

---

## First-time setup: suggest → review → promote → analyze

Column mappings are **human-approved**. The tool never silently applies a guess during analysis. This is a deliberate design decision — consistent with the Migration Plan's human-gate principle.

### Step 1 — Generate mapping suggestions

```bash
inventory-gap-analyzer suggest-mappings --input-dir /path/to/workbooks
```

Reads every `.xlsx` in the input directory, inspects column headers, and fuzzy-matches them against the canonical schema. Writes `config/column_mappings.suggested.yaml`. Each entry includes:

- The suggested canonical field name
- A fuzzy-match score (0–100)
- A confidence label: `high` (>85), `medium` (>65), `low` (>50), or `unmapped` (<50)

### Step 2 — Review the suggestions

Open `config/column_mappings.suggested.yaml`. Check every `low`-confidence and `unmapped` entry. Correct wrong matches; set the canonical value to `null` for columns that should not map to anything.

### Step 3 — Promote to the approved file

Copy your reviewed entries into `config/column_mappings.yaml` under the `mappings:` key:

```yaml
mappings:
  FWS_Systems_List.xlsx:
    System Name: application_name
    POC Email: application_owner_email
    Cloud Platform: cloud_provider
```

### Step 4 — Run the analysis

```bash
inventory-gap-analyzer analyze --input-dir /path/to/workbooks
```

Outputs are written to `./output/` (gitignored).

> **Quick look without promoting:** add `--use-suggested` to analyze straight from the suggested mappings. Good for a first pass; not a substitute for the review step.

---

## Commands

```
inventory-gap-analyzer suggest-mappings
    --input-dir PATH        Directory containing .xlsx workbooks
    [--config-dir PATH]     Defaults to ./config

inventory-gap-analyzer analyze
    --input-dir PATH
    [--output-dir PATH]         Defaults to ./output
    [--config-dir PATH]         Defaults to ./config
    [--include FILE]...         Limit to specific workbook filenames (repeatable)
    [--exclude FILE]...         Skip specific workbooks (repeatable)
    [--sparse-threshold FLOAT]  Population rate below which a mapped field is flagged sparse (default: 0.5)
    [--include-optional]        Include optional fields in missing_count (default: required only)
    [--regenerate-mappings]     Re-run suggest-mappings before analyzing, use the result
    [--use-suggested]           Use column_mappings.suggested.yaml instead of approved mappings
```

---

## Output files

All outputs land in `./output/` (configurable with `--output-dir`). The directory is gitignored.

| File | What it tells you |
|---|---|
| `coverage_matrix.csv` / `.xlsx` | Grid of bureaus × canonical fields. Each cell is the % of records with a real (non-placeholder) value. `—` means the column wasn't present at all. Color-coded in the Excel version. |
| `record_gaps.csv` | **One row per source application record.** Columns: bureau, workbook, sheet, row number, app name, semicolon-delimited list of missing required fields, missing count, owner email, whether each gap is researchable. This is the file you filter and sort to drive owner outreach. |
| `by_bureau/<Name>.md` | Per-bureau report: sheet selected and why, column mapping table, structural gaps, sparse fields, unmapped source columns, top 10 records with the most missing fields. |
| `dashboard.html` | Self-contained interactive HTML. Double-click to open — no server, no network. Heatmap overview, bureau drill-down, field drill-down, CSV export buttons. |
| `run.log` | Audit trail: every sheet-selection decision, every mapping applied, every assumption. No silent transformations. |

---

## Key concepts

**Structural gap** — a required canonical field with no mapped source column in a given workbook. This is a conversation with the bureau lead, not an individual owner.

**Sparse field** — a mapped field whose population rate is below the `--sparse-threshold` (default 50%). This means the column exists but most records don't have a value.

**Researchable vs owner-input** — each canonical field is tagged in `config/canonical_schema.yaml` as `researchable: true/false`. Fields like `url`, `description`, and `hosting_type` can often be filled from public sources during extraction. Fields like `ato_status`, `fisma_level`, and `annual_cost` require the application owner. The gap report surfaces this distinction so you know which path to take for each missing value.

**Placeholder detection** — these values are treated as null-equivalent: `N/A`, `TBD`, `Unknown`, `None`, `null`, `-`, `--`, whitespace-only strings. Checked case-insensitively after `strip()`. The full list is configurable in `config/placeholders.yaml`.

---

## Config files

| File | Purpose |
|---|---|
| `config/canonical_schema.yaml` | The locked 21-field schema. Each field has `type`, `required`, `researchable`, `null_ok`, and `synonyms` used for fuzzy matching. Do not modify the field list without a schema version bump. |
| `config/column_mappings.yaml` | Your human-approved `{ filename: { source_column: canonical_field } }` mappings. The tool will not run `analyze` without this (unless `--use-suggested`). |
| `config/column_mappings.suggested.yaml` | Tool-generated. Overwritten on every `suggest-mappings` run. Never applied automatically. |
| `config/sheet_selection.yaml` | Per-workbook sheet overrides. Example: `BLM_Application_Hosting_Inventory.xlsx: Technologies`. |
| `config/placeholders.yaml` | Null-equivalent strings. |

### Sheet selection logic

When a workbook has multiple sheets the tool never silently picks the first one. Order of precedence:

1. Explicit override in `config/sheet_selection.yaml`
2. Heuristic: the sheet with the most rows + most non-null cells + a column that looks like an application name
3. Every decision — including the reasoning — is written to `run.log`

### Bureau naming

Derived from the workbook filename. Common suffixes (`_Application_Inventory`, `_Systems_List`, `_Application_Hosting_Inventory`, etc.) are stripped and the first component is kept. Example: `BLM_Application_Hosting_Inventory.xlsx` → `BLM`.

---

## Running the tests

```bash
pytest tests/ -v
```

Tests build tiny synthetic `.xlsx` fixtures at runtime and cover: ingest and sheet selection, fuzzy mapping and confidence scoring, placeholder detection and coverage math, and report output formats. All runs are deterministic (collections are sorted before processing).

---

## What this tool does NOT do

These are explicitly out of scope to keep the tool focused:

- Generate upload-ready JSON (that's the extraction pipeline)
- Perform web research to fill in missing fields (that's the extraction phase)
- Modify source workbooks in any way (strictly read-only)
- Deduplicate records across bureaus
- Send notifications or emails to application owners
- Require a network connection or external API
