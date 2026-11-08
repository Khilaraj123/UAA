"""Validator for audit report and coverage ledger artifacts."""

import sys
import json
from pathlib import Path
from typing import List
from validators.schema_validator import validate_schema

LEDGER_SCHEMA = Path(__file__).parents[1] / "schemas" / "coverage-ledger.schema.json"

def validate_ledger_file(file_path: Path) -> List[str]:
    if not file_path.exists():
        return [f"File not found: {file_path}"]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Invalid JSON in {file_path}: {e}"]

    with open(LEDGER_SCHEMA, "r", encoding="utf-8") as sf:
        schema = json.load(sf)

    return validate_schema(data, schema)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m validators.validate_report <path_to_coverage_ledger.json>")
        sys.exit(1)
    errs = validate_ledger_file(Path(sys.argv[1]))
    if errs:
        print("❌ Coverage ledger validation failed:")
        for err in errs:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ Coverage ledger validation passed.")

