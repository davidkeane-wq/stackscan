from __future__ import annotations

from pathlib import Path

from stackscan.models import ScanReport, ScanResult
from stackscan.scanners.security.python import PythonScanner
from stackscan.scanners.security.terraform import TerraformScanner

# Add scanner instances here to activate them.
# The category field on each result determines security vs code_quality grouping;
# no changes to this file's structure are needed to support new categories.
_ACTIVE_SCANNERS = [
    TerraformScanner(),
    PythonScanner(),
]


def run(
    root_dir: str | Path,
    repo: str = "",
    commit_sha: str = "",
) -> ScanReport:
    """
    Discover and run all active scanners, aggregating results into a ScanReport.
    A failing scanner is logged but never aborts the whole run.
    """
    root_dir = Path(root_dir).resolve()
    findings: list[ScanResult] = []

    for scanner in _ACTIVE_SCANNERS:
        try:
            print(f"[stackscan] running scanner: {scanner.name}", flush=True)
            results = scanner.scan(root_dir)
            print(
                f"[stackscan] {scanner.name}: {len(results)} finding(s)",
                flush=True,
            )
            findings.extend(results)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[stackscan] scanner '{scanner.name}' failed: {exc}",
                flush=True,
            )

    return ScanReport(repo=repo, commit_sha=commit_sha, findings=findings)
