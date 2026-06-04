"""inventory-gap-analyzer: coverage & gap analysis for application inventory workbooks."""

from pathlib import Path

import yaml

__version__ = "0.1.0"

# Default config dir bundled with the package (repo-relative).
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning {} for empty/missing files."""
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


def load_schema_fields(config_dir: Path) -> list[dict]:
    """Load the canonical schema field definitions (ordered)."""
    data = load_yaml(Path(config_dir) / "canonical_schema.yaml")
    return list(data.get("fields", []))


def load_placeholders(config_dir: Path) -> list[str]:
    """Load null-equivalent placeholder strings."""
    data = load_yaml(Path(config_dir) / "placeholders.yaml")
    return list(data.get("placeholders", []))


def load_sheet_selection(config_dir: Path) -> dict:
    """Load per-workbook sheet overrides (basename -> sheet name)."""
    data = load_yaml(Path(config_dir) / "sheet_selection.yaml")
    # The file is a flat mapping; drop comment-only / non-dict content.
    return {k: v for k, v in data.items()} if isinstance(data, dict) else {}
