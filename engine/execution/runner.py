"""Deterministic, standard-library HTTP execution runner for UAA."""

import datetime as dt
import json
import os
import re
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPHandler, HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from engine.assertions.evaluator import evaluate_assertion

VERSION = "2.0.0"
MAX_BODY_BYTES = 2_000_000
SECRET_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "proxy-authorization",
    "x-auth-token",
    "x-amz-security-token",
}
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def expand_env(value: Any) -> Any:
    """Expand ${ENV_VAR} patterns. Fails closed if variable is missing."""
    if isinstance(value, str):
        def _replace(match):
            key = match.group(1)
            if key not in os.environ:
                raise ValueError(f"Missing required environment variable for execution: '{key}'")
            return os.environ[key]
        return ENV_PATTERN.sub(_replace, value)
    if isinstance(value, list):
        return [expand_env(x) for x in value]
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    return value

def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Redact secret header values."""
    return {k: ("[REDACTED]" if k.lower() in SECRET_HEADERS else v) for k, v in headers.items()}

def redact_json(value: Any, extra_keys: Optional[Set[str]] = None) -> Any:
    """Recursively redact sensitive keys in JSON structures."""
    hidden = {
        "password", "token", "access_token", "refresh_token",
        "secret", "api_key", "apikey", "private_key", "client_secret"
    }
    if extra_keys:
        hidden.update(k.lower() for k in extra_keys)

    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if k.lower() in hidden else redact_json(v, extra_keys))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_json(x, extra_keys) for x in value]
    return value

class SuppressRedirectHandler(HTTPRedirectHandler):
    """Prevent automated redirect following to evaluate 3xx assertions directly."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def execute_scenario(
    base_url: str,
    scenario: Dict[str, Any],
    default_timeout: float = 10.0,
    redact_keys: Optional[Set[str]] = None,
    allow_destructive: bool = False,
) -> Dict[str, Any]:
    """Execute a single scenario deterministically."""
    scenario_id = scenario.get("scenario_id", "UNKNOWN")
    endpoint_id = scenario.get("endpoint_id", "UNKNOWN")
    safety = scenario.get("safety", {})
    enabled = scenario.get("enabled", True)

    # Safety checks
    if not enabled:
        return {
            "scenario_id": scenario_id,
            "endpoint_id": endpoint_id,
            "outcome": "skipped",
            "passed": False,
            "skip_reason": scenario.get("skip_reason") or "Scenario marked disabled",
            "http_status": None,
            "duration_ms": 0.0,
            "request": None,
            "response": None,
            "assertions": [],
        }

    is_destructive = safety.get("is_destructive", False) or safety.get("has_external_effects", False)
    if is_destructive and not allow_destructive:
        return {
            "scenario_id": scenario_id,
            "endpoint_id": endpoint_id,
            "outcome": "skipped",
            "passed": False,
            "skip_reason": "Destructive or external-effect scenario blocked by safety gate (use --allow-destructive to override)",
            "http_status": None,
            "duration_ms": 0.0,
            "request": None,
            "response": None,
            "assertions": [],
        }

    req_def = scenario.get("request", {})
    try:
        resolved_req = expand_env(req_def)
    except ValueError as e:
        return {
            "scenario_id": scenario_id,
            "endpoint_id": endpoint_id,
            "outcome": "error",
            "passed": False,
            "error_message": str(e),
            "http_status": None,
            "duration_ms": 0.0,
            "request": None,
            "response": None,
            "assertions": [],
        }

    method = resolved_req.get("method", "GET").upper()
    path = resolved_req.get("path", "/")
    target_url = base_url.rstrip("/") + (path if path.startswith("/") else "/" + path)

    if resolved_req.get("query"):
        q_str = urlencode(resolved_req["query"], doseq=True)
        target_url += ("&" if "?" in target_url else "?") + q_str

    parsed = urlsplit(target_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return {
            "scenario_id": scenario_id,
            "endpoint_id": endpoint_id,
            "outcome": "error",
            "passed": False,
            "error_message": f"Invalid URL target scheme: {parsed.scheme}",
            "http_status": None,
            "duration_ms": 0.0,
            "request": None,
            "response": None,
            "assertions": [],
        }

    req_headers = dict(resolved_req.get("headers", {}))
    body = resolved_req.get("body")
    encoded_body = None
    if body is not None:
        if isinstance(body, str):
            encoded_body = body.encode("utf-8")
        else:
            encoded_body = json.dumps(body).encode("utf-8")
        if not any(k.lower() == "content-type" for k in req_headers):
            req_headers["Content-Type"] = "application/json"

    timeout = min(float(resolved_req.get("timeout_seconds", default_timeout)), 60.0)

    http_req = Request(target_url, data=encoded_body, headers=req_headers, method=method)
    ssl_ctx = ssl.create_default_context()
    opener = build_opener(
        ProxyHandler(),
        SuppressRedirectHandler(),
        HTTPSHandler(context=ssl_ctx),
        HTTPHandler(),
    )

    start_time = time.monotonic()
    raw_response = b""
    resp_status = 500
    resp_headers: Dict[str, str] = {}
    error_msg = None

    try:
        response = opener.open(http_req, timeout=timeout)
        resp_status = response.status
        resp_headers = dict(response.headers.items())
        raw_response = response.read(MAX_BODY_BYTES + 1)
    except HTTPError as e:
        resp_status = e.code
        resp_headers = dict(e.headers.items())
        raw_response = e.read(MAX_BODY_BYTES + 1)
    except URLError as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        return {
            "scenario_id": scenario_id,
            "endpoint_id": endpoint_id,
            "outcome": "error",
            "passed": False,
            "error_message": f"Network/Connection error: {e.reason}",
            "http_status": None,
            "duration_ms": duration_ms,
            "request": {
                "method": method,
                "path": path,
                "headers": redact_headers(req_headers),
            },
            "response": None,
            "assertions": [],
        }
    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        return {
            "scenario_id": scenario_id,
            "endpoint_id": endpoint_id,
            "outcome": "error",
            "passed": False,
            "error_message": f"Execution failure: {str(e)}",
            "http_status": None,
            "duration_ms": duration_ms,
            "request": {
                "method": method,
                "path": path,
                "headers": redact_headers(req_headers),
            },
            "response": None,
            "assertions": [],
        }

    duration_ms = round((time.monotonic() - start_time) * 1000, 2)
    truncated = len(raw_response) > MAX_BODY_BYTES
    body_text = raw_response[:MAX_BODY_BYTES].decode("utf-8", errors="replace")

    body_json = None
    if body_text:
        try:
            body_json = json.loads(body_text)
        except json.JSONDecodeError:
            pass

    # Assertions evaluation
    assertions_specs = scenario.get("assertions", [])
    assertion_results = [
        evaluate_assertion(a, resp_status, resp_headers, body_text, body_json)
        for a in assertions_specs
    ]

    all_passed = len(assertion_results) > 0 and all(a["passed"] for a in assertion_results)

    clean_response_body = (
        redact_json(body_json, redact_keys)
        if body_json is not None
        else body_text[:4000]
    )

    return {
        "scenario_id": scenario_id,
        "endpoint_id": endpoint_id,
        "outcome": "passed" if all_passed else "failed",
        "passed": all_passed,
        "skip_reason": None,
        "error_message": error_msg,
        "http_status": resp_status,
        "duration_ms": duration_ms,
        "request": {
            "method": method,
            "path": path,
            "headers": redact_headers(req_headers),
        },
        "response": {
            "status": resp_status,
            "headers": redact_headers(resp_headers),
            "body": clean_response_body,
            "body_truncated": truncated,
        },
        "assertions": assertion_results,
    }

class ExecutionRunner:
    """Executes a test specification suite against a target origin."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        allow_destructive: bool = False,
        redact_keys: Optional[Set[str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.allow_destructive = allow_destructive
        self.redact_keys = redact_keys or set()

    def run_suite(self, spec: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
        spec_id = spec.get("specification_id", "SPEC-001")
        scenarios = list(spec.get("scenarios", []))

        # Deterministic execution order: lexical sort by scenario_id
        scenarios.sort(key=lambda s: s.get("scenario_id", ""))

        if not run_id:
            timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
            run_id = f"run_{timestamp}"

        started_at = dt.datetime.now(dt.timezone.utc).isoformat()
        results: List[Dict[str, Any]] = []

        total_duration = 0.0
        passed_count = 0
        failed_count = 0
        skipped_count = 0
        error_count = 0

        for sc in scenarios:
            res = execute_scenario(
                base_url=self.base_url,
                scenario=sc,
                default_timeout=self.timeout,
                redact_keys=self.redact_keys,
                allow_destructive=self.allow_destructive,
            )
            results.append(res)
            total_duration += res.get("duration_ms", 0.0) or 0.0

            outcome = res.get("outcome")
            if outcome == "passed":
                passed_count += 1
            elif outcome == "failed":
                failed_count += 1
            elif outcome == "skipped":
                skipped_count += 1
            elif outcome == "error":
                error_count += 1

        completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
        total_executed = passed_count + failed_count
        pass_rate = round((passed_count / total_executed * 100), 2) if total_executed > 0 else 0.0

        return {
            "schema_version": "2.0.0",
            "run_id": run_id,
            "specification_id": spec_id,
            "target_origin": self.base_url,
            "runner_version": VERSION,
            "started_at": started_at,
            "completed_at": completed_at,
            "summary": {
                "total": len(scenarios),
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "errors": error_count,
                "pass_rate": pass_rate,
                "total_duration_ms": round(total_duration, 2),
            },
            "results": results,
        }

