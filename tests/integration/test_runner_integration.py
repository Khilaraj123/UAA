import unittest
import threading
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from engine.execution.runner import ExecutionRunner, expand_env, redact_headers, redact_json

class MockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Custom-Header", "UAA-Test")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "mock-api"}).encode())
        elif self.path == "/api/v1/protected":
            auth = self.headers.get("Authorization")
            if auth == "Bearer valid-token":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"secret_data": 42}).encode())
            else:
                self.send_response(401)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/v1/items":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            parsed = json.loads(body.decode()) if body else {}
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": 101, "name": parsed.get("name")}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress HTTP server console logs in tests

class TestRunnerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), MockAPIHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_environment_expansion(self):
        os.environ["UAA_TEST_VAR"] = "test-secret-value"
        self.assertEqual(expand_env("${UAA_TEST_VAR}"), "test-secret-value")
        with self.assertRaises(ValueError):
            expand_env("${NON_EXISTENT_UAA_VAR}")

    def test_redaction(self):
        headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}
        redacted = redact_headers(headers)
        self.assertEqual(redacted["Authorization"], "[REDACTED]")
        self.assertEqual(redacted["Content-Type"], "application/json")

        body = {"password": "secret", "user": "alice"}
        self.assertEqual(redact_json(body)["password"], "[REDACTED]")

    def test_execution_suite_against_mock_server(self):
        spec = {
            "specification_id": "TEST-SPEC-MOCK",
            "scenarios": [
                {
                    "scenario_id": "SCEN-001",
                    "endpoint_id": "rest:GET:/health",
                    "title": "Health check",
                    "category": "happy_path",
                    "priority": "P0",
                    "request": {"method": "GET", "path": "/health"},
                    "assertions": [
                        {"type": "status", "expected": 200},
                        {"type": "header_equals", "name": "x-custom-header", "expected": "UAA-Test"},
                        {"type": "json_equals", "path": "status", "expected": "ok"},
                    ],
                    "safety": {"is_safe_read": True, "has_external_effects": False, "is_destructive": False},
                    "enabled": True,
                },
                {
                    "scenario_id": "SCEN-002",
                    "endpoint_id": "rest:POST:/api/v1/items",
                    "title": "Create item",
                    "category": "happy_path",
                    "priority": "P0",
                    "request": {
                        "method": "POST",
                        "path": "/api/v1/items",
                        "body": {"name": "Test Gadget"},
                    },
                    "assertions": [
                        {"type": "status", "expected": 201},
                        {"type": "json_equals", "path": "name", "expected": "Test Gadget"},
                        {"type": "json_equals", "path": "id", "expected": 101},
                    ],
                    "safety": {"is_safe_read": False, "has_external_effects": False, "is_destructive": False},
                    "enabled": True,
                },
            ],
        }

        runner = ExecutionRunner(base_url=self.base_url)
        results = runner.run_suite(spec)

        self.assertEqual(results["summary"]["total"], 2)
        self.assertEqual(results["summary"]["passed"], 2)
        self.assertEqual(results["summary"]["failed"], 0)
        self.assertEqual(results["summary"]["pass_rate"], 100.0)

if __name__ == "__main__":
    unittest.main()

