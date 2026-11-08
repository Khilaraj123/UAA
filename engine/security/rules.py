"""Automated security rules and analyzers for UAA."""

from typing import Any, Dict, List, Optional
from engine.security.findings import Finding, FindingStore

class SecurityAnalyzer:
    """Analyzes endpoint inventory and execution results to detect API vulnerabilities."""

    def __init__(self, finding_store: Optional[FindingStore] = None):
        self.store = finding_store or FindingStore()

    def analyze_inventory(self, inventory: Dict[str, Any]) -> FindingStore:
        endpoints = inventory.get("endpoints", [])
        for ep in endpoints:
            self._check_unauthenticated_sensitive_endpoints(ep)
            self._check_potential_bola_idor(ep)
            self._check_mass_assignment_indicators(ep)
        return self.store

    def analyze_execution_results(self, results: Dict[str, Any]) -> FindingStore:
        scenario_results = results.get("results", [])
        for res in scenario_results:
            self._check_data_leakage(res)
            self._check_stack_trace_leakage(res)
            self._check_missing_security_headers(res)
        return self.store

    def _check_unauthenticated_sensitive_endpoints(self, ep: Dict[str, Any]) -> None:
        path = ep.get("path_template", "").lower()
        method = ep.get("method", "").upper()
        auth = ep.get("authentication", {})
        is_auth_required = auth.get("required", False)

        sensitive_keywords = ["admin", "user", "account", "billing", "payment", "internal", "secret", "token"]
        is_sensitive = any(kw in path for kw in sensitive_keywords) or (method in ("DELETE", "PUT", "PATCH"))

        if not is_auth_required and is_sensitive:
            ep_id = ep.get("endpoint_id")
            fid = f"FIND-AUTH-{abs(hash(ep_id)) % 10000:04d}"
            self.store.add_finding(Finding(
                finding_id=fid,
                title="Sensitive Endpoint Appears Unauthenticated",
                severity="high",
                category="broken_authentication",
                endpoint_id=ep_id,
                status="open",
                description=f"Endpoint '{method} {ep.get('path_template')}' manages sensitive functionality but is declared with no authentication requirement.",
                impact="Unauthenticated remote attackers can access or manipulate sensitive resources without credentials.",
                evidence={
                    "claim_type": "contract_inspection",
                    "explanation": f"Endpoint declared with authentication.required=false on sensitive route '{ep.get('path_template')}'.",
                },
                remediation={
                    "guidance": "Enforce authentication middleware or decorator on this route and require verified JWT/session.",
                    "reference_urls": ["https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/"],
                },
                cwe_id="CWE-306",
                owasp_api_category="API2:2023 Broken Authentication",
            ))

    def _check_potential_bola_idor(self, ep: Dict[str, Any]) -> None:
        path = ep.get("path_template", "")
        auth = ep.get("authentication", {})
        tenant_isolated = auth.get("tenant_isolated", False)

        if "{" in path and "}" in path and not tenant_isolated:
            ep_id = ep.get("endpoint_id")
            fid = f"FIND-BOLA-{abs(hash(ep_id)) % 10000:04d}"
            self.store.add_finding(Finding(
                finding_id=fid,
                title="Potential Broken Object Level Authorization (BOLA/IDOR)",
                severity="high",
                category="bola_idor",
                endpoint_id=ep_id,
                status="open",
                description=f"Endpoint '{ep.get('method')} {path}' accepts an object ID directly in the path without documented tenant or ownership boundary isolation.",
                impact="An authenticated user may access or modify resources belonging to other tenants/users by changing the ID parameter.",
                evidence={
                    "claim_type": "contract_inspection",
                    "explanation": f"Parameterized path '{path}' has tenant_isolated=false in authentication metadata.",
                },
                remediation={
                    "guidance": "Verify that resource lookups in domain/persistence logic strictly enforce the authenticated principal's tenant/user ID scope.",
                    "reference_urls": ["https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/"],
                },
                cwe_id="CWE-639",
                owasp_api_category="API1:2023 Broken Object Level Authorization",
            ))

    def _check_mass_assignment_indicators(self, ep: Dict[str, Any]) -> None:
        method = ep.get("method", "").upper()
        if method in ("POST", "PUT", "PATCH"):
            body = ep.get("request_body")
            if body and body.get("schema"):
                schema = body["schema"]
                # If schema has additionalProperties not set to false or accepts role/is_admin
                props = schema.get("properties", {})
                risky_fields = {"role", "is_admin", "admin", "permissions", "balance", "credit", "verified"}
                found_risky = set(props.keys()).intersection(risky_fields)
                if found_risky:
                    ep_id = ep.get("endpoint_id")
                    fid = f"FIND-MASS-{abs(hash(ep_id)) % 10000:04d}"
                    self.store.add_finding(Finding(
                        finding_id=fid,
                        title="Mass Assignment Risk via Privileged Body Properties",
                        severity="medium",
                        category="mass_assignment",
                        endpoint_id=ep_id,
                        status="open",
                        description=f"Endpoint accepts client-supplied properties {list(found_risky)} which control privileges or authorization state.",
                        impact="Clients may elevate privileges or modify protected attributes during standard create/update operations.",
                        evidence={
                            "claim_type": "contract_inspection",
                            "explanation": f"Request body schema defines privileged properties: {list(found_risky)}.",
                        },
                        remediation={
                            "guidance": "Use separate Data Transfer Objects (DTOs) for creation/update and exclude privilege-granting attributes from client binding.",
                            "reference_urls": ["https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/"],
                        },
                        cwe_id="CWE-915",
                        owasp_api_category="API6:2023 Server-Side Request Forgery / Mass Assignment",
                    ))

    def _check_data_leakage(self, res: Dict[str, Any]) -> None:
        response = res.get("response")
        if not response:
            return
        body = response.get("body")
        body_str = str(body).lower()

        leakage_patterns = ["password_hash", "private_key", "secret_key", "db_password", "aws_secret_access_key"]
        for pat in leakage_patterns:
            if pat in body_str:
                scen_id = res.get("scenario_id")
                ep_id = res.get("endpoint_id")
                fid = f"FIND-LEAK-{abs(hash(scen_id)) % 10000:04d}"
                self.store.add_finding(Finding(
                    finding_id=fid,
                    title="Sensitive Credential/Key Leakage in API Response",
                    severity="critical",
                    category="data_exposure",
                    endpoint_id=ep_id,
                    status="confirmed",
                    description=f"Response body contains pattern '{pat}' in scenario {scen_id}.",
                    impact="Direct disclosure of system credentials or cryptographic secrets to API consumers.",
                    evidence={
                        "claim_type": "observed_execution",
                        "reproducing_scenario_id": scen_id,
                        "explanation": f"Matched leak indicator '{pat}' in observed response.",
                    },
                    remediation={
                        "guidance": "Ensure response serialization DTOs explicitly exclude sensitive internal fields.",
                    },
                    cwe_id="CWE-200",
                    owasp_api_category="API3:2023 Broken Object Property Level Authorization",
                ))

    def _check_stack_trace_leakage(self, res: Dict[str, Any]) -> None:
        response = res.get("response")
        if not response:
            return
        status = response.get("status", 0)
        body = response.get("body")
        body_str = str(body)

        trace_indicators = [
            "traceback (most recent call last)",
            "at System.Web.",
            "at Microsoft.AspNetCore.",
            "express/lib/router",
            "node_modules",
            "NullReferenceException",
            "UnhandledException",
        ]
        if status >= 500 and any(ti in body_str for ti in trace_indicators):
            scen_id = res.get("scenario_id")
            ep_id = res.get("endpoint_id")
            fid = f"FIND-ERR-{abs(hash(scen_id)) % 10000:04d}"
            self.store.add_finding(Finding(
                finding_id=fid,
                title="Unhandled Exception Stack Trace Leaked to Client",
                severity="medium",
                category="unhandled_exception",
                endpoint_id=ep_id,
                status="confirmed",
                description=f"HTTP {status} response returned internal runtime stack trace in scenario {scen_id}.",
                impact="Internal implementation paths, library versions, and architectural topology leaked to potential attackers.",
                evidence={
                    "claim_type": "observed_execution",
                    "reproducing_scenario_id": scen_id,
                    "explanation": "Observed stack trace signatures in HTTP 500 error body.",
                },
                remediation={
                    "guidance": "Configure global exception handling middleware to suppress internal stack traces in non-development modes and return RFC 7807 Problem Details.",
                },
                cwe_id="CWE-209",
                owasp_api_category="API8:2023 Security Misconfiguration",
            ))

    def _check_missing_security_headers(self, res: Dict[str, Any]) -> None:
        response = res.get("response")
        if not response:
            return
        headers = response.get("headers", {})
        headers_lower = {k.lower(): v for k, v in headers.items()}

        recommended_headers = [
            ("x-content-type-options", "nosniff", "Missing X-Content-Type-Options: nosniff header"),
            ("x-frame-options", None, "Missing X-Frame-Options header"),
        ]
        for h_name, expected_val, msg in recommended_headers:
            if h_name not in headers_lower:
                ep_id = res.get("endpoint_id")
                fid = f"FIND-HDR-{abs(hash(ep_id + h_name)) % 10000:04d}"
                if fid not in self.store.findings:
                    self.store.add_finding(Finding(
                        finding_id=fid,
                        title=msg,
                        severity="low",
                        category="security_misconfiguration",
                        endpoint_id=ep_id,
                        status="confirmed",
                        description=f"Response does not supply security header '{h_name}'.",
                        impact="Client browser may be susceptible to MIME confusion attacks or clickjacking.",
                        evidence={
                            "claim_type": "observed_execution",
                            "reproducing_scenario_id": res.get("scenario_id"),
                            "explanation": f"Header '{h_name}' missing from HTTP response headers.",
                        },
                        remediation={
                            "guidance": f"Add '{h_name}' to global API response headers middleware.",
                        },
                        cwe_id="CWE-16",
                        owasp_api_category="API8:2023 Security Misconfiguration",
                    ))

