"""GraphQL protocol runner adapter."""

from typing import Any, Dict
from adapters.protocols.base import BaseProtocolAdapter
from engine.execution.runner import execute_scenario

class GraphQLProtocolAdapter(BaseProtocolAdapter):
    @property
    def protocol_name(self) -> str:
        return "graphql"

    def execute(self, target_origin: str, scenario: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        # Wrap GraphQL scenario into HTTP POST request format if necessary
        req = dict(scenario.get("request", {}))
        if "query" in req and "body" not in req:
            req["method"] = "POST"
            req["body"] = {
                "query": req["query"],
                "variables": req.get("variables", {}),
            }
            scenario["request"] = req

        return execute_scenario(
            base_url=target_origin,
            scenario=scenario,
            default_timeout=timeout,
        )

