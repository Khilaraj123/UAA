"""Validator for API endpoint inventory artifacts."""

import sys
import json
from pathlib import Path
from typing import List
from validators.schema_validator import validate_schema

SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "inventory.schema.json"

def validate_inventory_file(file_path: Path) -> List[str]:
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

    # Domain specific verification: ensure every endpoint has unique endpoint_id
    seen_ids = set()
    for i, ep in enumerate(data.get("endpoints", [])):
        eid = ep.get("endpoint_id")
        if eid in seen_ids:
            errors.append(f"endpoints[{i}]: duplicate endpoint_id '{eid}'")
        seen_ids.add(eid)

        if not ep.get("source_evidence"):
            errors.append(f"endpoints[{i}] ({eid}): must provide at least one source_evidence entry")

    return errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m validators.validate_inventory <path_to_inventory.json>")
        sys.exit(1)
    errs = validate_inventory_file(Path(sys.argv[1]))
    if errs:
        print("❌ Inventory validation failed:")
        for err in errs:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ Inventory validation passed.")

