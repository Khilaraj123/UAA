"""Discovery adapters package for UAA."""
from adapters.discovery.base import BaseDiscoveryAdapter
from adapters.discovery.fastapi.fastapi_adapter import FastAPIDiscoveryAdapter
from adapters.discovery.express.express_adapter import ExpressDiscoveryAdapter
from adapters.discovery.dotnet.dotnet_adapter import DotNetDiscoveryAdapter

DISCOVERY_ADAPTERS = [
    FastAPIDiscoveryAdapter(),
    ExpressDiscoveryAdapter(),
    DotNetDiscoveryAdapter(),
]

__all__ = [
    "BaseDiscoveryAdapter",
    "FastAPIDiscoveryAdapter",
    "ExpressDiscoveryAdapter",
    "DotNetDiscoveryAdapter",
    "DISCOVERY_ADAPTERS",
]

