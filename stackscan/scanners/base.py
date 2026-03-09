from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stackscan.models import ScanResult


class BaseScanner(ABC):
    """Abstract base class for all stackscan scanners."""

    name: str
    category: str  # "security" | "code_quality"

    @abstractmethod
    def collect(self, root_dir: str | Path) -> list[tuple[str, str]]:
        """
        Discover files relevant to this scanner.

        Returns a list of (relative_file_path, file_content) tuples.
        """
        ...

    @abstractmethod
    def scan(self, root_dir: str | Path) -> list[ScanResult]:
        """
        Run analysis on the target directory.

        Returns a list of ScanResult instances.
        """
        ...
