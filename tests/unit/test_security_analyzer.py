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

if __name__ == "__main__":
    unittest.main()

