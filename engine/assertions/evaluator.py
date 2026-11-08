"""Assertion evaluation engine for Universal API Assurance."""

from typing import Any, Dict, List, Optional, Tuple

def get_json_path(value: Any, path: Optional[str]) -> Any:
    """Traverse JSON object/array using dotted keys and numeric array indices."""
    if not path or path in ("", "$"):
        return value
    clean_path = path
    if clean_path.startswith("$."):
        clean_path = clean_path[2:]
    elif clean_path.startswith("$"):
        clean_path = clean_path[1:]

    parts = clean_path.split(".")
    curr = value
    for part in parts:
        if not part:
            continue
        if isinstance(curr, list):
            if part.isdigit():
                curr = curr[int(part)]
            else:
                raise KeyError(f"Cannot index array with non-integer property '{part}'")
        elif isinstance(curr, dict):
            if part in curr:
                curr = curr[part]
            else:
                raise KeyError(f"Key '{part}' not found in object")
        else:
            raise TypeError(f"Cannot traverse into primitive {type(curr).__name__} for '{part}'")
    return curr

def get_value_type(val: Any) -> str:
    """Determine JSON schema type string."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, (int, float)):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, list):
        return "array"
    if isinstance(val, dict):
        return "object"
    return "unknown"

def evaluate_assertion(
    assertion: Dict[str, Any],
    status: int,
    headers: Dict[str, str],
    body_text: str,
    body_json: Any,
) -> Dict[str, Any]:
    """Evaluate a single test assertion and return detailed outcome."""
    kind = assertion.get("type", "")
    expected = assertion.get("expected")
    path = assertion.get("path")
    target_name = assertion.get("name")
    
    passed = False
    actual = None
    message = ""

    headers_lower = {k.lower(): v for k, v in headers.items()}

    try:
        if kind == "status":
            actual = status
            passed = (status == int(expected))
            message = f"Expected status {expected}, received {status}"

        elif kind == "header_equals":
            if not target_name:
                raise ValueError("header_equals requires 'name' property")
            header_key = target_name.lower()
            actual = headers_lower.get(header_key)
            passed = (actual is not None and str(actual) == str(expected))
            message = f"Header '{target_name}' expected '{expected}', found '{actual}'"

        elif kind == "header_exists":
            if not target_name:
                raise ValueError("header_exists requires 'name' property")
            header_key = target_name.lower()
            actual = header_key in headers_lower
            passed = actual
            message = f"Header '{target_name}' {'exists' if actual else 'does not exist'}"

        elif kind == "content_type":
            actual = headers_lower.get("content-type")
            if actual is None:
                passed = False
                message = f"Content-Type header missing, expected containing '{expected}'"
            else:
                passed = str(expected).lower() in actual.lower()
                message = f"Content-Type '{actual}' matches '{expected}'"

        elif kind == "json_equals":
            actual = get_json_path(body_json, path)
            passed = (actual == expected)
            message = f"Path '{path}' expected {repr(expected)}, got {repr(actual)}"

        elif kind == "json_exists":
            try:
                actual = get_json_path(body_json, path)
                passed = True
                message = f"Path '{path}' exists"
            except (KeyError, IndexError, TypeError):
                passed = False
                actual = None
                message = f"Path '{path}' not found in JSON response"

        elif kind == "json_type":
            val = get_json_path(body_json, path)
            actual = get_value_type(val)
            passed = (actual == str(expected).lower())
            message = f"Path '{path}' expected type '{expected}', got '{actual}'"

        elif kind == "text_contains":
            actual = body_text[:1000] if body_text else ""
            exp_str = str(expected)
            passed = exp_str in body_text
            message = f"Body {'contains' if passed else 'does not contain'} '{exp_str}'"

        elif kind == "text_not_contains":
            actual = body_text[:1000] if body_text else ""
            exp_str = str(expected)
            passed = exp_str not in body_text
            message = f"Body {'correctly excludes' if passed else 'unexpectedly contains'} '{exp_str}'"

        else:
            message = f"Unsupported assertion type: '{kind}'"
            passed = False

    except Exception as err:
        passed = False
        message = f"Evaluation error: {str(err)}"

    return {
        "type": kind,
        "path": path,
        "name": target_name,
        "expected": expected,
        "actual": actual,
        "passed": bool(passed),
        "message": message,
    }

