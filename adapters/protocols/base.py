"""Base protocol runner interface for UAA."""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseProtocolAdapter(ABC):
    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Protocol name, e.g., 'http', 'graphql', 'grpc', 'websocket'."""
        pass

    @abstractmethod
    def execute(self, target_origin: str, scenario: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        """Execute request and return standardized execution result."""
        pass

