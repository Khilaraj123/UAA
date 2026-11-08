import unittest
from pathlib import Path
from adapters.discovery.fastapi.fastapi_adapter import FastAPIDiscoveryAdapter
from adapters.discovery.express.express_adapter import ExpressDiscoveryAdapter
from adapters.discovery.dotnet.dotnet_adapter import DotNetDiscoveryAdapter

class TestFrameworkAdapters(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parents[2] / "fixtures"

    def test_fastapi_adapter(self):
        adapter = FastAPIDiscoveryAdapter()
        fastapi_dir = self.fixtures_dir / "fastapi"
        self.assertTrue(adapter.detect(fastapi_dir))
        endpoints = adapter.discover(fastapi_dir)
        methods_paths = [(ep.method, ep.path_template) for ep in endpoints]
        self.assertIn(("GET", "/health"), methods_paths)
        self.assertIn(("GET", "/api/v1/items"), methods_paths)
        self.assertIn(("GET", "/api/v1/items/{item_id}"), methods_paths)
        self.assertIn(("POST", "/api/v1/items"), methods_paths)

    def test_express_adapter(self):
        adapter = ExpressDiscoveryAdapter()
        express_dir = self.fixtures_dir / "express"
        endpoints = adapter.discover(express_dir)
        methods_paths = [(ep.method, ep.path_template) for ep in endpoints]
        self.assertIn(("GET", "/health"), methods_paths)
        self.assertIn(("GET", "/users"), methods_paths)
        self.assertIn(("GET", "/users/{id}"), methods_paths)
        self.assertIn(("POST", "/users"), methods_paths)

    def test_dotnet_adapter(self):
        adapter = DotNetDiscoveryAdapter()
        dotnet_dir = self.fixtures_dir / "dotnet"
        endpoints = adapter.discover(dotnet_dir)
        methods_paths = [(ep.method, ep.path_template) for ep in endpoints]
        self.assertIn(("GET", "/health"), methods_paths)
        self.assertIn(("GET", "/api/v1/products"), methods_paths)
        self.assertIn(("GET", "/api/v1/users"), methods_paths)
        self.assertIn(("GET", "/api/v1/users/{id}"), methods_paths)

if __name__ == "__main__":
    unittest.main()

