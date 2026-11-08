"""Lightweight zero-dependency JSON Schema & contract validator for UAA."""

from typing import Any, Dict, List, Optional, Tuple
import json
import re

def validate_types(val: Any, expected_types: Any) -> bool:
    if isinstance(expected_types, str):
        expected_types = [expected_types]
    for t in expected_types:
        if t == "string" and isinstance(val, str):
            return True
        if t == "integer" and isinstance(val, int) and not isinstance(val, bool):
            return True
        if t == "number" and isinstance(val, (int, float)) and not isinstance(val, bool):
            return True
        if t == "boolean" and isinstance(val, bool):
            return True
        if t == "array" and isinstance(val, list):
            return True
        if t == "object" and isinstance(val, dict):
            return True
        if t == "null" and val is None:
            return True
    return False

def validate_schema(data: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Validate JSON data against basic JSON Schema rules (required, types, enums, properties)."""
    errors: List[str] = []

    # Check type
    if "type" in schema:
        if not validate_types(data, schema["type"]):
            errors.append(f"{path}: expected type {schema['type']}, got {type(data).__name__}")
            return errors

    # Check enum
    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(f"{path}: value '{data}' not in allowed enum values {schema['enum']}")

    # Check const
    if "const" in schema:
        if data != schema["const"]:
            errors.append(f"{path}: expected constant '{schema['const']}', got '{data}'")

    # If object
    if isinstance(data, dict):
        # Required fields
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"{path}: missing required property '{req}'")

        # Properties
        prop_schemas = schema.get("properties", {})
        for prop_name, prop_val in data.items():
            if prop_name in prop_schemas:
                sub_errors = validate_schema(prop_val, prop_schemas[prop_name], f"{path}.{prop_name}")
                errors.extend(sub_errors)

    # If array
    if isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema and isinstance(item_schema, dict):
            for i, item in enumerate(data):
                sub_errors = validate_schema(item, item_schema, f"{path}[{i}]")
                errors.extend(sub_errors)

    return errors

