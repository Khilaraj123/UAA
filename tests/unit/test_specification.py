import unittest
from engine.specification.models import (
    Endpoint,
    SourceEvidence,
    normalize_path,
    make_endpoint_id,
)

class TestSpecificationModels(unittest.TestCase):
    def test_normalize_path(self):
        self.assertEqual(normalize_path("/users/:id"), "/users/{id}")
        self.assertEqual(normalize_path("users/<int:id>/posts"), "/users/{id}/posts")
        self.assertEqual(normalize_path("/items/"), "/items")
        self.assertEqual(normalize_path("/"), "/")

    def test_make_endpoint_id(self):
        eid = make_endpoint_id("REST", "get", "/api/v1/users/:id")
        self.assertEqual(eid, "rest:GET:/api/v1/users/{id}")

    def test_endpoint_serialization(self):
        ep = Endpoint(
            endpoint_id="rest:GET:/health",
            api_type="rest",
            method="GET",
            path_template="/health",
            discovery_status="confirmed",
            confidence="high",
            source_evidence=[SourceEvidence(
                source_type="framework_route",
                file_path="main.py",
                confidence="high",
            )],
        )
        d = ep.to_dict()
        self.assertEqual(d["endpoint_id"], "rest:GET:/health")
        self.assertEqual(d["source_evidence"][0]["source_type"], "framework_route")

if __name__ == "__main__":
    unittest.main()

