"""Validator for execution result artifacts."""

import sys
import json
from pathlib import Path
from typing import List
from validators.schema_validator import validate_schema

SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "execution.schema.json"

def validate_execution_file(file_path: Path) -> List[str]:
    if not file_path.exists():
        return [f"File not found: {file_path}"]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Invalid JSON in {file_path}: {e}"]

    with open(SCHEMA_PATH, "r", encoding="utf-8") as sf:
        schema = json.load(sf)

    errors = validate_schema(data, schema)

    # Validate summary counts match results list
    summary = data.get("summary", {})
    results = data.get("results", [])

    if len(results) != summary.get("total"):
        errors.append(f"Summary total ({summary.get('total')}) does not match results array length ({len(results)})")

    return errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m validators.validate_execution <path_to_execution_results.json>")
        sys.exit(1)
    errs = validate_execution_file(Path(sys.argv[1]))
    if errs:
        print("❌ Execution validation failed:")
        for err in errs:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ Execution validation passed.")

