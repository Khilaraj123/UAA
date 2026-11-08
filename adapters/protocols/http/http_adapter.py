"""HTTP/REST protocol runner adapter."""

from typing import Any, Dict
from adapters.protocols.base import BaseProtocolAdapter
from engine.execution.runner import execute_scenario

class HttpProtocolAdapter(BaseProtocolAdapter):
    @property
    def protocol_name(self) -> str:
        return "http"

    def execute(self, target_origin: str, scenario: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        return execute_scenario(
            base_url=target_origin,
            scenario=scenario,
            default_timeout=timeout,
        )

