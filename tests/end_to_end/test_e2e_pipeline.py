import unittest
import threading
import json
import shutil
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

from adapters.discovery.fastapi.fastapi_adapter import FastAPIDiscoveryAdapter
from engine.execution.runner import ExecutionRunner
from engine.coverage.ledger import CoverageLedgerBuilder
from engine.security.rules import SecurityAnalyzer
from engine.reporting.reporter import generate_markdown_report, generate_html_dashboard

class MockFastAPIServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        elif self.path.startswith("/api/v1/items"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'[{"id":1,"name":"Widget","price":9.99}]')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

class TestE2EPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), MockFastAPIServer)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_complete_audit_lifecycle(self):
        # 1. Discovery
        adapter = FastAPIDiscoveryAdapter()
        repo_path = Path(__file__).parents[2] / "fixtures" / "fastapi"
        endpoints = adapter.discover(repo_path)
        self.assertGreater(len(endpoints), 0)

        inventory_data = {
            "schema_version": "2.0.0",
            "generated_at": "2026-11-08T00:00:00Z",
            "completeness": "high",
            "discovery_sources": [
                {
                    "source_layer": 2,
                    "source_name": "FastAPI Route AST",
                    "inspected": True,
                    "endpoints_found": len(endpoints),
                }
            ],
            "endpoints": [ep.to_dict() for ep in endpoints],
        }

        # 2. Design Spec
        spec = {
            "specification_id": "SPEC-E2E-001",
            "scenarios": [
                {
                    "scenario_id": "SCEN-001-HEALTH",
                    "endpoint_id": "rest:GET:/health",
                    "title": "Health Check returns 200",
                    "category": "happy_path",
                    "priority": "P0",
                    "request": {"method": "GET", "path": "/health"},
                    "assertions": [
                        {"type": "status", "expected": 200},
                        {"type": "json_equals", "path": "status", "expected": "ok"},
                    ],
                    "safety": {"is_safe_read": True, "has_external_effects": False, "is_destructive": False},
                    "enabled": True,
                },
                {
                    "scenario_id": "SCEN-002-ITEMS",
                    "endpoint_id": "rest:GET:/api/v1/items",
                    "title": "List Items returns 200",
                    "category": "happy_path",
                    "priority": "P0",
                    "request": {"method": "GET", "path": "/api/v1/items"},
                    "assertions": [
                        {"type": "status", "expected": 200},
                        {"type": "json_type", "path": "$", "expected": "array"},
                    ],
                    "safety": {"is_safe_read": True, "has_external_effects": False, "is_destructive": False},
                    "enabled": True,
                },
            ],
        }

        # 3. Execution
        runner = ExecutionRunner(base_url=self.base_url)
        exec_results = runner.run_suite(spec, run_id="run-e2e")
        self.assertEqual(exec_results["summary"]["passed"], 2)

        # 4. Coverage Ledger
        ledger_builder = CoverageLedgerBuilder(run_id="run-e2e")
        ledger_builder.record_source("FastAPI AST", 2, "complete", files_scanned=1, endpoints_yielded=len(endpoints))
        for ep in endpoints:
            eid = ep.endpoint_id
            ledger_builder.record_discovery(eid, ep.method, ep.path_template)
            ledger_builder.record_understanding(eid, status="complete")

        # Record executed
        ledger_builder.record_scenarios("rest:GET:/health", 1, ["happy_path"])
        ledger_builder.record_execution("rest:GET:/health", executed=1, passed=1, failed=0, skipped=0)

        ledger_builder.record_scenarios("rest:GET:/api/v1/items", 1, ["happy_path"])
        ledger_builder.record_execution("rest:GET:/api/v1/items", executed=1, passed=1, failed=0, skipped=0)

        ledger = ledger_builder.build()
        self.assertEqual(ledger["metrics"]["endpoints_verified_pass"], 2)

        # 5. Security Analysis
        sec_analyzer = SecurityAnalyzer()
        sec_analyzer.analyze_inventory(inventory_data)
        sec_analyzer.analyze_execution_results(exec_results)
        findings = sec_analyzer.store.list_all()

        # 6. Reports Generation
        md_report = generate_markdown_report(inventory_data, exec_results, ledger, findings, trend=None)
        html_dashboard = generate_html_dashboard(inventory_data, exec_results, ledger, findings, trend=None)

        self.assertIn("Universal API Assurance (UAA) - Audit Report", md_report)
        self.assertIn("<!DOCTYPE html>", html_dashboard)
        self.assertIn("Endpoint Explorer", html_dashboard)
        self.assertIn("Security Findings", html_dashboard)

if __name__ == "__main__":
    unittest.main()

