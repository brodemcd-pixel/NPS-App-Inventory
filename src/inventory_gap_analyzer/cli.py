"""Click entrypoint for inventory-gap-analyzer."""

from __future__ import annotations

from pathlib import Path

import click

from . import (
    DEFAULT_CONFIG_DIR,
    load_placeholders,
    load_schema_fields,
    load_sheet_selection,
)
from .coverage import compute_coverage
from .dashboard import generate_dashboard
from .ingest import load_workbooks
from .mapping import load_mappings, suggest_mappings
from .reports import (
    write_bureau_reports,
    write_coverage_matrix,
    write_record_gaps,
    write_run_log,
)


@click.group()
@click.version_option()
def main() -> None:
    """Coverage & gap analysis for application inventory workbooks."""


@main.command("suggest-mappings")
@click.option(
    "--input-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory containing .xlsx workbooks.",
)
@click.option(
    "--config-dir",
    default=str(DEFAULT_CONFIG_DIR),
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory with config YAML files.",
)
def suggest_mappings_cmd(input_dir: Path, config_dir: Path) -> None:
    """Generate config/column_mappings.suggested.yaml from fuzzy matching."""
    schema_fields = load_schema_fields(config_dir)
    sheet_selection = load_sheet_selection(config_dir)
    workbooks = load_workbooks(input_dir, sheet_selection=sheet_selection)
    if not workbooks:
        click.echo(f"No .xlsx workbooks found in {input_dir}", err=True)
        raise SystemExit(1)
    suggest_mappings(workbooks, schema_fields, config_dir)
    out = Path(config_dir) / "column_mappings.suggested.yaml"
    click.echo(f"Wrote suggestions for {len(workbooks)} workbook(s) to {out}")
    click.echo("Review and promote approved entries into column_mappings.yaml.")


@main.command("analyze")
@click.option(
    "--input-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory containing .xlsx workbooks.",
)
@click.option(
    "--output-dir",
    default="output",
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory for generated reports (created if missing).",
)
@click.option(
    "--config-dir",
    default=str(DEFAULT_CONFIG_DIR),
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory with config YAML files.",
)
@click.option("--include", multiple=True, help="Only include these workbook filenames.")
@click.option("--exclude", multiple=True, help="Exclude these workbook filenames.")
@click.option(
    "--sparse-threshold",
    default=0.5,
    type=float,
    help="Population rate below which a mapped field is 'sparse'.",
)
@click.option("--include-optional", is_flag=True, help="Include optional fields in summaries.")
@click.option(
    "--regenerate-mappings",
    is_flag=True,
    help="Regenerate suggested mappings before analyzing.",
)
@click.option(
    "--use-suggested",
    is_flag=True,
    help="Use column_mappings.suggested.yaml instead of the approved file.",
)
def analyze_cmd(
    input_dir: Path,
    output_dir: Path,
    config_dir: Path,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    sparse_threshold: float,
    include_optional: bool,
    regenerate_mappings: bool,
    use_suggested: bool,
) -> None:
    """Run the full coverage & gap analysis, writing reports and a dashboard."""
    schema_fields = load_schema_fields(config_dir)
    placeholders = load_placeholders(config_dir)
    sheet_selection = load_sheet_selection(config_dir)

    if not include_optional:
        # include_optional only widens summaries; full schema always evaluated.
        pass

    workbooks = load_workbooks(
        input_dir,
        include=list(include) or None,
        exclude=list(exclude) or None,
        sheet_selection=sheet_selection,
    )
    if not workbooks:
        click.echo(f"No .xlsx workbooks found in {input_dir}", err=True)
        raise SystemExit(1)

    log_entries: list[str] = []
    for wb in workbooks:
        log_entries.extend(wb.log)

    if regenerate_mappings:
        suggest_mappings(workbooks, schema_fields, config_dir)
        log_entries.append("Regenerated column_mappings.suggested.yaml")
        use_suggested = True

    mappings = load_mappings(config_dir, use_suggested=use_suggested)
    if not mappings:
        source = "suggested" if use_suggested else "approved"
        click.echo(
            f"No {source} column mappings found. Run 'suggest-mappings', review, "
            "and populate config/column_mappings.yaml (or pass --use-suggested).",
            err=True,
        )
        raise SystemExit(1)

    results = []
    for wb in sorted(workbooks, key=lambda w: w.bureau):
        res = compute_coverage(
            wb, mappings, schema_fields, placeholders, sparse_threshold=sparse_threshold
        )
        results.append(res)
        log_entries.append(
            f"[{wb.bureau}] {res.total_records} records, "
            f"{len(res.structural_gaps)} structural gap(s), "
            f"{len(res.sparse_fields)} sparse field(s)"
        )

    write_coverage_matrix(results, output_dir)
    write_record_gaps(results, output_dir)
    write_bureau_reports(results, output_dir)
    generate_dashboard(results, output_dir)
    write_run_log(log_entries, output_dir)

    click.echo(f"Analyzed {len(results)} bureau(s). Reports written to {output_dir}/")
    click.echo(f"  - {output_dir}/coverage_matrix.csv / .xlsx")
    click.echo(f"  - {output_dir}/record_gaps.csv")
    click.echo(f"  - {output_dir}/bureaus/*.md")
    click.echo(f"  - {output_dir}/dashboard.html")
    click.echo(f"  - {output_dir}/run.log")


if __name__ == "__main__":
    main()
