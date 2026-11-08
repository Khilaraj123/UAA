import unittest
import os
from engine.execution.runner import redact_headers, redact_json, expand_env
from engine.assertions.evaluator import get_json_path, evaluate_assertion

class TestRunnerLegacy(unittest.TestCase):
    def test_json_path_and_assertion(self):
        obj = {'items': [{'id': 9}]}
        self.assertEqual(get_json_path(obj, 'items.0.id'), 9)
        res = evaluate_assertion({'type': 'json_equals', 'path': 'items.0.id', 'expected': 9}, 200, {}, '', obj)
        self.assertTrue(res['passed'])

    def test_redaction(self):
        self.assertEqual(redact_headers({'Authorization': 'Bearer x'})['Authorization'], '[REDACTED]')
        self.assertEqual(redact_json({'password': 'x', 'visible': 'y'})['password'], '[REDACTED]')

    def test_missing_env_fails_closed(self):
        if 'API_AUDIT_MISSING_TEST' in os.environ:
            del os.environ['API_AUDIT_MISSING_TEST']
        with self.assertRaises(ValueError):
            expand_env('${API_AUDIT_MISSING_TEST}')

if __name__ == '__main__':
    unittest.main()
