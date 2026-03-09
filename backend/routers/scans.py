from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models import ScanReport

router = APIRouter(prefix="/api/v1")

BUCKET_NAME = os.environ.get("SCAN_RESULTS_BUCKET", "")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "")

# Local storage dir used when SCAN_RESULTS_BUCKET is not set.
_LOCAL_DIR = Path(os.environ.get("LOCAL_STORAGE_DIR", "/tmp/stackscan-scans"))

_bearer = HTTPBearer()


def _verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> None:
    expected = os.environ.get("DASHBOARD_TOKEN", "")
    if not expected or credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


def _use_local() -> bool:
    return not BUCKET_NAME


# ── Local filesystem storage ────────────────────────────────────────────────

def _local_write(scan_id: str, data: str) -> None:
    _LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    (_LOCAL_DIR / f"{scan_id}.json").write_text(data, encoding="utf-8")


def _local_read(scan_id: str) -> dict[str, Any]:
    path = _LOCAL_DIR / f"{scan_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _local_list() -> list[dict[str, Any]]:
    if not _LOCAL_DIR.exists():
        return []
    files = sorted(_LOCAL_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for f in files[:50]:
        try:
            results.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    return results


# ── GCS storage ─────────────────────────────────────────────────────────────

def _gcs_client():
    from google.cloud import storage  # deferred so local mode never imports it
    project = os.environ.get("GCP_PROJECT")
    return storage.Client(project=project)


def _gcs_write(scan_id: str, data: str) -> None:
    client = _gcs_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"scans/{scan_id}.json")
    blob.upload_from_string(data, content_type="application/json")


def _gcs_read(scan_id: str) -> dict[str, Any]:
    client = _gcs_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"scans/{scan_id}.json")
    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    return json.loads(blob.download_as_text())


def _gcs_list() -> list[dict[str, Any]]:
    client = _gcs_client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = sorted(
        client.list_blobs(bucket, prefix="scans/"),
        key=lambda b: b.time_created,
        reverse=True,
    )[:50]
    results = []
    for blob in blobs:
        try:
            results.append(json.loads(blob.download_as_text()))
        except Exception:  # noqa: BLE001
            pass
    return results


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/scans", status_code=201)
async def create_scan(
    report: ScanReport,
    request: Request,
    _: None = Depends(_verify_token),
) -> dict[str, str]:
    scan_id = str(report.scan_id)
    data = report.model_dump_json()

    if _use_local():
        _local_write(scan_id, data)
    else:
        _gcs_write(scan_id, data)

    base = DASHBOARD_URL.rstrip("/") if DASHBOARD_URL else str(request.base_url).rstrip("/")
    return {"scan_id": scan_id, "report_url": f"{base}/scans/{scan_id}"}


@router.get("/scans")
async def list_scans() -> list[dict[str, Any]]:
    return _local_list() if _use_local() else _gcs_list()


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str) -> dict[str, Any]:
    return _local_read(scan_id) if _use_local() else _gcs_read(scan_id)
