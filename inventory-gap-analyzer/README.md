# inventory-gap-analyzer

A Python CLI that measures **coverage and structural gaps** in application-inventory
workbooks against a locked 21-field canonical schema (modeled on the NPS / DOI
application inventory migration). It maps each workbook's columns to canonical
fields, computes how well each field is populated per bureau, and emits CSV,
per-bureau Markdown, and a self-contained HTML dashboard.

## Installation

```bash
pip install -e .
```

Requires Python >= 3.11.

## First-time setup flow

Mappings are **human-approved**: the tool never guesses silently for analysis.
The flow is suggest -> review -> promote -> analyze.

1. **Generate suggestions** from your workbooks:

   ```bash
   inventory-gap-analyzer suggest-mappings --input-dir /path/to/workbooks
   ```

   This writes `config/column_mappings.suggested.yaml`. Each source column gets a
   suggested canonical field, a fuzzy-match `score`, and a `confidence` label
   (`high` > 85, `medium` > 65, `low` > 50, else `unmapped`).

2. **Review** the suggested file. Correct any wrong matches; set the canonical
   value to `null` for columns that should not map.

3. **Promote** the approved entries into `config/column_mappings.yaml` under the
   `mappings:` key. Format:

   ```yaml
   mappings:
     ParkService_Application_Inventory.xlsx:
       Application Name: application_name
       Description: description
       Owner: application_owner
   ```

4. **Analyze**:

   ```bash
   inventory-gap-analyzer analyze --input-dir /path/to/workbooks
   ```

   To analyze straight from suggestions without promoting (e.g. a quick look),
   add `--use-suggested`.

## Commands

```
inventory-gap-analyzer suggest-mappings --input-dir PATH [--config-dir PATH]

inventory-gap-analyzer analyze --input-dir PATH [--output-dir PATH]
    [--config-dir PATH] [--include FILE]... [--exclude FILE]...
    [--sparse-threshold FLOAT] [--include-optional]
    [--regenerate-mappings] [--use-suggested]
```

- `--include` / `--exclude` — filter workbooks by filename (repeatable).
- `--sparse-threshold` — population rate below which a *mapped* field is flagged
  sparse (default `0.5`).
- `--regenerate-mappings` — re-run suggestions before analyzing and use them.
- `--use-suggested` — analyze with `column_mappings.suggested.yaml`.

## Output files (`output/`, gitignored)

| File | Meaning |
| --- | --- |
| `coverage_matrix.csv` / `.xlsx` | Bureaus x canonical fields, population rate per cell. |
| `record_gaps.csv` | One row per (bureau, field): populated/missing counts, rate, distinct values, structural-gap and sparse flags. |
| `bureaus/<Bureau>.md` | Per-bureau report: field coverage table, structural gaps, sparse fields, unmapped source columns. |
| `dashboard.html` | Self-contained interactive dashboard (heatmap, bureau drill-down, field drill-down, CSV export). No network calls. |
| `run.log` | Every sheet-selection decision and run summary. |

## Concepts

- **Structural gap** — a *required* canonical field with no mapped source column.
- **Sparse field** — a mapped field whose population rate is below the threshold.
- **Placeholder** — a null-equivalent string (`N/A`, `TBD`, `Unknown`, `-`, ...),
  matched case-insensitively after `strip()`. Configurable in
  `config/placeholders.yaml`.

## Config reference (`config/`)

| File | Purpose |
| --- | --- |
| `canonical_schema.yaml` | The locked 21 canonical fields with `type`, `required`, `researchable`, `null_ok`, and `synonyms` used for fuzzy matching. |
| `column_mappings.yaml` | Human-approved `{ filename: { source_column: canonical_field } }` mappings. |
| `sheet_selection.yaml` | Per-workbook sheet overrides (`filename.xlsx: SheetName`). |
| `placeholders.yaml` | Null-equivalent strings. |

### Sheet selection

When a workbook has multiple sheets the tool never silently picks the first one.
It checks `sheet_selection.yaml` first, then a heuristic that prefers the sheet
with an application-name-like column, the most non-null cells, and the most rows.
Every decision is logged to `run.log`.

### Bureau naming

The bureau is derived from the workbook filename: common suffixes such as
`_Application_Inventory`, `_Systems_List`, `_Application_Hosting_Inventory` are
stripped and the first component is kept (e.g.
`BLM_Application_Hosting_Inventory.xlsx` -> `BLM`).

## Tests

```bash
pytest tests/ -v
```

Tests build tiny synthetic `.xlsx` fixtures at runtime and cover ingest/sheet
selection, fuzzy mapping, placeholder detection / coverage math, and report
output formats. Runs are deterministic (collections are sorted before
processing).
