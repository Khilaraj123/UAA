"""Base interface for UAA framework discovery adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from engine.specification.models import Endpoint

class BaseDiscoveryAdapter(ABC):
    """Abstract base class for language/framework endpoint discovery adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the adapter (e.g., 'fastapi', 'express', 'dotnet')."""
        pass

    @abstractmethod
    def detect(self, repo_path: Path) -> bool:
        """Determine if target repository uses this framework."""
        pass

    @abstractmethod
    def discover(self, repo_path: Path) -> List[Endpoint]:
        """Discover and return endpoints from the target repository."""
        pass

