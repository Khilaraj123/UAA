"""Validator for test specification artifacts."""

import sys
import json
from pathlib import Path
from typing import List
from validators.schema_validator import validate_schema

SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "testspec.schema.json"

def validate_testspec_file(file_path: Path) -> List[str]:
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

    # Domain specific validation
    scenarios = data.get("scenarios", [])
    seen_ids = set()
    for i, s in enumerate(scenarios):
        sid = s.get("scenario_id")
        if sid in seen_ids:
            errors.append(f"scenarios[{i}]: duplicate scenario_id '{sid}'")
        seen_ids.add(sid)

        # Ensure safety object presence
        safety = s.get("safety", {})
        if not isinstance(safety, dict):
            errors.append(f"scenarios[{i}] ({sid}): safety must be an object with boolean flags")

    return errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m validators.validate_testspec <path_to_testspec.json>")
        sys.exit(1)
    errs = validate_testspec_file(Path(sys.argv[1]))
    if errs:
        print("❌ Testspec validation failed:")
        for err in errs:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ Testspec validation passed.")

