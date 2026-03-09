from __future__ import annotations

import httpx

from stackscan.models import ScanReport


def post_report(report: ScanReport, dashboard_url: str, token: str) -> dict:
    """
    POST a ScanReport to the dashboard API.

    Returns the parsed JSON response, which includes ``scan_id`` and
    ``report_url``.  Raises ``httpx.HTTPStatusError`` on non-2xx responses.
    """
    url = dashboard_url.rstrip("/") + "/api/v1/scans"
    response = httpx.post(
        url,
        content=report.model_dump_json(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
