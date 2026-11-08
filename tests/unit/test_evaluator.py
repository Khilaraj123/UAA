import unittest
from engine.assertions.evaluator import evaluate_assertion, get_json_path, get_value_type

class TestAssertionEvaluator(unittest.TestCase):
    def test_json_path_navigation(self):
        data = {
            "users": [
                {"id": 1, "profile": {"name": "Alice"}},
                {"id": 2, "profile": {"name": "Bob"}},
            ],
            "count": 2,
        }
        self.assertEqual(get_json_path(data, "count"), 2)
        self.assertEqual(get_json_path(data, "users.0.id"), 1)
        self.assertEqual(get_json_path(data, "users.1.profile.name"), "Bob")
        self.assertEqual(get_json_path(data, "$.users.0.profile.name"), "Alice")

    def test_assertion_status(self):
        res = evaluate_assertion({"type": "status", "expected": 200}, 200, {}, "", None)
        self.assertTrue(res["passed"])

        res_fail = evaluate_assertion({"type": "status", "expected": 200}, 404, {}, "", None)
        self.assertFalse(res_fail["passed"])

    def test_assertion_headers(self):
        headers = {"Content-Type": "application/json; charset=utf-8", "X-Request-Id": "req-99"}
        self.assertTrue(evaluate_assertion({"type": "header_exists", "name": "x-request-id"}, 200, headers, "", None)["passed"])
        self.assertTrue(evaluate_assertion({"type": "content_type", "expected": "application/json"}, 200, headers, "", None)["passed"])

    def test_assertion_json(self):
        body = {"status": "ok", "items": [10, 20]}
        self.assertTrue(evaluate_assertion({"type": "json_equals", "path": "status", "expected": "ok"}, 200, {}, "", body)["passed"])
        self.assertTrue(evaluate_assertion({"type": "json_exists", "path": "items.1"}, 200, {}, "", body)["passed"])
        self.assertTrue(evaluate_assertion({"type": "json_type", "path": "items", "expected": "array"}, 200, {}, "", body)["passed"])

    def test_assertion_text(self):
        body_text = "Internal Server Error at line 42"
        self.assertTrue(evaluate_assertion({"type": "text_contains", "expected": "Internal Server Error"}, 500, {}, body_text, None)["passed"])
        self.assertTrue(evaluate_assertion({"type": "text_not_contains", "expected": "password_hash"}, 200, {}, body_text, None)["passed"])

if __name__ == "__main__":
    unittest.main()

