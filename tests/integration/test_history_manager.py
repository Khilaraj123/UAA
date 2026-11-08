import unittest
import shutil
from pathlib import Path
from engine.reporting.history import RunHistoryManager

class TestRunHistoryManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("api-audit-test-history")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.mgr = RunHistoryManager(base_audit_dir=str(self.test_dir))

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_run_numbering_and_regression(self):
        run1 = self.mgr.get_next_run_id()
        self.assertEqual(run1, "run-001")

        # Save run 1 results (1 scenario passed)
        exec1 = {
            "run_id": "run-001",
            "summary": {"pass_rate": 100.0},
            "results": [
                {"scenario_id": "SCEN-01", "endpoint_id": "rest:GET:/health", "passed": True}
            ],
        }
        self.mgr.save_run_artifact("run-001", "execution-results.json", exec1)

        # Run 2
        run2 = self.mgr.get_next_run_id()
        self.assertEqual(run2, "run-002")

        # Save run 2 results (scenario regressed and failed)
        exec2 = {
            "run_id": "run-002",
            "summary": {"pass_rate": 0.0},
            "results": [
                {"scenario_id": "SCEN-01", "endpoint_id": "rest:GET:/health", "passed": False}
            ],
        }
        self.mgr.save_run_artifact("run-002", "execution-results.json", exec2)

        # Compare runs
        diff = self.mgr.compare_runs("run-001", "run-002")
        self.assertEqual(diff["status"], "compared")
        self.assertEqual(diff["regression_count"], 1)
        self.assertEqual(diff["regressions"][0]["scenario_id"], "SCEN-01")
        self.assertEqual(diff["pass_rate_delta"], -100.0)

if __name__ == "__main__":
    unittest.main()

