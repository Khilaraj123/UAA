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

    def test_compare_runs_detects_missing_and_new_scenarios(self):
        # Run 1: SCEN-01 (passed), SCEN-02 (passed)
        exec1 = {
            "run_id": "run-001",
            "summary": {"pass_rate": 100.0},
            "results": [
                {"scenario_id": "SCEN-01", "endpoint_id": "rest:GET:/health", "passed": True},
                {"scenario_id": "SCEN-02", "endpoint_id": "rest:GET:/users", "passed": True},
            ],
        }
        self.mgr.save_run_artifact("run-001", "execution-results.json", exec1)

        # Run 2:
        # SCEN-01 still passed
        # SCEN-02 is MISSING (deleted/lost coverage)
        # SCEN-03 is NEW and PASSED
        # SCEN-04 is NEW and FAILED
        exec2 = {
            "run_id": "run-002",
            "summary": {"pass_rate": 66.7},
            "results": [
                {"scenario_id": "SCEN-01", "endpoint_id": "rest:GET:/health", "passed": True},
                {"scenario_id": "SCEN-03", "endpoint_id": "rest:POST:/orders", "passed": True},
                {"scenario_id": "SCEN-04", "endpoint_id": "rest:POST:/checkout", "passed": False},
            ],
        }
        self.mgr.save_run_artifact("run-002", "execution-results.json", exec2)

        diff = self.mgr.compare_runs("run-001", "run-002")
        self.assertEqual(diff["status"], "compared")

        # Missing scenarios (coverage loss)
        self.assertEqual(diff["missing_scenario_count"], 1)
        self.assertEqual(diff["missing_scenarios"][0]["scenario_id"], "SCEN-02")
        self.assertTrue(diff["missing_scenarios"][0]["previously_passed"])

        # New scenarios
        self.assertEqual(diff["new_scenario_count"], 2)
        new_ids = {n["scenario_id"]: n["passed"] for n in diff["new_scenarios"]}
        self.assertEqual(new_ids, {"SCEN-03": True, "SCEN-04": False})

        # Regressions should flag both the missing scenario (coverage loss) and new failure
        reg_ids = [r["scenario_id"] for r in diff["regressions"]]
        self.assertIn("SCEN-02", reg_ids)  # coverage loss regression
        self.assertIn("SCEN-04", reg_ids)  # new failing scenario regression
        self.assertEqual(diff["regression_count"], 2)

if __name__ == "__main__":
    unittest.main()

