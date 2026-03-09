from __future__ import annotations

from pathlib import Path

from stackscan.models import ScanResult
from stackscan.scanners.base import BaseScanner


class PlaceholderQualityScanner(BaseScanner):
    """
    Stub code-quality scanner — ready for a real implementation.

    To activate:
    1. Implement collect() and scan() with your analysis logic.
    2. Add an instance to _ACTIVE_SCANNERS in stackscan/runner.py.
    """

    name = "quality"
    category = "code_quality"

    def collect(self, root_dir: str | Path) -> list[tuple[str, str]]:
        return []

    def scan(self, root_dir: str | Path) -> list[ScanResult]:
        return []
