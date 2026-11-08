"""Protocol adapters package for UAA."""
from adapters.protocols.base import BaseProtocolAdapter
from adapters.protocols.http.http_adapter import HttpProtocolAdapter
from adapters.protocols.graphql.graphql_adapter import GraphQLProtocolAdapter

PROTOCOL_ADAPTERS = {
    "http": HttpProtocolAdapter(),
    "rest": HttpProtocolAdapter(),
    "graphql": GraphQLProtocolAdapter(),
}

__all__ = [
    "BaseProtocolAdapter",
    "HttpProtocolAdapter",
    "GraphQLProtocolAdapter",
    "PROTOCOL_ADAPTERS",
]

