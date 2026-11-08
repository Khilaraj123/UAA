# UAA Extension Guide: Adding Discovery & Protocol Adapters

Universal API Assurance is designed to be easily extensible to new programming languages, web frameworks, and communication protocols without altering the core assurance engine.

## 1. Adding a New Discovery Adapter

Discovery adapters reside in `adapters/discovery/<framework_name>/` and inherit from `BaseDiscoveryAdapter`.

### Step 1: Implement the Class
```python
from pathlib import Path
from typing import List
from adapters.discovery.base import BaseDiscoveryAdapter
from engine.specification.models import Endpoint, SourceEvidence, make_endpoint_id, normalize_path

class GoGinDiscoveryAdapter(BaseDiscoveryAdapter):
    @property
    def name(self) -> str:
        return "gin"

    def detect(self, repo_path: Path) -> bool:
        # Check go.mod or .go files for gin-gonic/gin
        return any("github.com/gin-gonic/gin" in f.read_text(errors="ignore") for f in repo_path.glob("go.mod"))

    def discover(self, repo_path: Path) -> List[Endpoint]:
        endpoints = []
        # Parse Go AST or regex for r.GET("/path", handler)
        # Return list of canonical Endpoint objects
        return endpoints
```

### Step 2: Register in `adapters/discovery/__init__.py`
Add your adapter instance to `DISCOVERY_ADAPTERS`:
```python
from adapters.discovery.golang.gin_adapter import GoGinDiscoveryAdapter
DISCOVERY_ADAPTERS.append(GoGinDiscoveryAdapter())
```

---

## 2. Adding a New Protocol Adapter

Protocol adapters execute scenarios for specific network communication styles (e.g. gRPC, WebSocket, SSE) and inherit from `BaseProtocolAdapter` in `adapters/protocols/base.py`.

### Step 1: Implement the Class
```python
from typing import Any, Dict
from adapters.protocols.base import BaseProtocolAdapter

class GrpcProtocolAdapter(BaseProtocolAdapter):
    @property
    def protocol_name(self) -> str:
        return "grpc"

    def execute(self, target_origin: str, scenario: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        # Connect to gRPC channel, invoke RPC method, evaluate assertions, return result
        ...
```

### Step 2: Register in `adapters/protocols/__init__.py`
```python
PROTOCOL_ADAPTERS["grpc"] = GrpcProtocolAdapter()
```

