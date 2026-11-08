import unittest
from engine.coverage.ledger import CoverageLedgerBuilder

class TestCoverageLedger(unittest.TestCase):
    def test_coverage_ledger_progression(self):
        builder = CoverageLedgerBuilder(run_id="run-test")
        builder.record_source("FastAPI Routes", 2, "complete", files_scanned=5, endpoints_yielded=2)

        builder.record_discovery("rest:GET:/health", "GET", "/health")
        builder.record_discovery("rest:POST:/users", "POST", "/users")

        builder.record_understanding("rest:GET:/health", status="complete")
        builder.record_understanding("rest:POST:/users", status="complete")

        builder.record_scenarios("rest:GET:/health", 1, ["happy_path"])
        builder.record_scenarios("rest:POST:/users", 2, ["happy_path", "validation"])

        # Execute: health passes, users fails
        builder.record_execution("rest:GET:/health", executed=1, passed=1, failed=0, skipped=0)
        builder.record_execution("rest:POST:/users", executed=2, passed=1, failed=1, skipped=0)

        data = builder.build()
        metrics = data["metrics"]
        self.assertEqual(metrics["total_endpoints_discovered"], 2)
        self.assertEqual(metrics["endpoints_understood"], 2)
        self.assertEqual(metrics["endpoints_verified_pass"], 1)
        self.assertEqual(metrics["endpoints_unverified"], 1)
        self.assertEqual(metrics["coverage_ratio"], 0.5)

        # Ensure unverified reason recorded
        self.assertEqual(len(data["unverified_endpoints"]), 1)
        self.assertEqual(data["unverified_endpoints"][0]["endpoint_id"], "rest:POST:/users")

        # Test Markdown generation
        md = builder.to_markdown()
        self.assertIn("Coverage Ledger", md)
        self.assertIn("50.0%", md)

if __name__ == "__main__":
    unittest.main()

