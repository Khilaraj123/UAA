import unittest
from engine.security.rules import SecurityAnalyzer
from engine.security.findings import FindingStore

class TestSecurityAnalyzer(unittest.TestCase):
    def test_unauthenticated_sensitive_endpoint(self):
        analyzer = SecurityAnalyzer()
        inventory = {
            "endpoints": [
                {
                    "endpoint_id": "rest:DELETE:/api/v1/users/{id}",
                    "path_template": "/api/v1/users/{id}",
                    "method": "DELETE",
                    "authentication": {"required": False},
                }
            ]
        }
        store = analyzer.analyze_inventory(inventory)
        findings = store.list_all()
        self.assertTrue(any(f["category"] == "broken_authentication" for f in findings))
        self.assertTrue(any(f["category"] == "bola_idor" for f in findings))

    def test_execution_leakage_detection(self):
        analyzer = SecurityAnalyzer()
        results = {
            "results": [
                {
                    "scenario_id": "SCEN-001",
                    "endpoint_id": "rest:GET:/api/v1/users",
                    "response": {
                        "status": 200,
                        "headers": {"content-type": "application/json"},
                        "body": {"password_hash": "argon2$secret"},
                    },
                }
            ]
        }
        store = analyzer.analyze_execution_results(results)
        findings = store.list_all()
        self.assertTrue(any(f["category"] == "data_exposure" for f in findings))

    def test_finding_ids_are_deterministic(self):
        inventory = {
            "endpoints": [
                {
                    "endpoint_id": "rest:DELETE:/api/v1/users/{id}",
                    "path_template": "/api/v1/users/{id}",
                    "method": "DELETE",
                    "authentication": {"required": False, "tenant_isolated": False},
                },
                {
                    "endpoint_id": "rest:POST:/api/v1/admin/users",
                    "path_template": "/api/v1/admin/users",
                    "method": "POST",
                    "authentication": {"required": False},
                    "request_body": {
                        "schema": {
                            "properties": {"role": {"type": "string"}, "name": {"type": "string"}}
                        }
                    },
                },
            ]
        }
        results = {
            "results": [
                {
                    "scenario_id": "SCEN-001",
                    "endpoint_id": "rest:GET:/api/v1/users",
                    "response": {
                        "status": 500,
                        "headers": {},
                        "body": "UnhandledException: traceback (most recent call last) secret_key=123",
                    },
                }
            ]
        }

        # Analyze twice in separate analyzer instances
        analyzer1 = SecurityAnalyzer()
        analyzer1.analyze_inventory(inventory)
        analyzer1.analyze_execution_results(results)
        findings1 = {f["finding_id"]: f for f in analyzer1.store.list_all()}

        analyzer2 = SecurityAnalyzer()
        analyzer2.analyze_inventory(inventory)
        analyzer2.analyze_execution_results(results)
        findings2 = {f["finding_id"]: f for f in analyzer2.store.list_all()}

        # Verify exact same finding IDs are generated deterministically
        self.assertEqual(set(findings1.keys()), set(findings2.keys()))
        for fid, f1 in findings1.items():
            f2 = findings2[fid]
            self.assertEqual(f1["title"], f2["title"])
            self.assertEqual(f1["category"], f2["category"])
            self.assertEqual(f1["endpoint_id"], f2["endpoint_id"])
            # Format validation FIND-<TYPE>-XXXX
            self.assertRegex(fid, r"^FIND-[A-Z]+-\d{4}$")

    def test_finding_ids_across_different_python_hash_seeds(self):
        import subprocess
        import sys
        import os

        script = """
import json
from engine.security.rules import SecurityAnalyzer
inventory = {
    "endpoints": [
        {
            "endpoint_id": "rest:DELETE:/api/v1/users/{id}",
            "path_template": "/api/v1/users/{id}",
            "method": "DELETE",
            "authentication": {"required": False, "tenant_isolated": False},
        }
    ]
}
results = {
    "results": [
        {
            "scenario_id": "SCEN-001",
            "endpoint_id": "rest:GET:/api/v1/users",
            "response": {
                "status": 500,
                "headers": {},
                "body": "password_hash: argon2",
            },
        }
    ]
}
a = SecurityAnalyzer()
a.analyze_inventory(inventory)
a.analyze_execution_results(results)
print(json.dumps([f["finding_id"] for f in a.store.list_all()]))
"""
        env1 = dict(os.environ, PYTHONHASHSEED="1")
        env2 = dict(os.environ, PYTHONHASHSEED="99999")

        out1 = subprocess.check_output([sys.executable, "-c", script], env=env1).decode().strip()
        out2 = subprocess.check_output([sys.executable, "-c", script], env=env2).decode().strip()

        self.assertEqual(out1, out2)

if __name__ == "__main__":
    unittest.main()

