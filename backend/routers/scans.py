import os
import json
from fastapi import APIRouter, HTTPException
from google.cloud import storage

router = APIRouter()

BUCKET_NAME = os.environ.get("SCAN_RESULTS_BUCKET", "pipeline-dashboard-scan-results")

def get_scan_report(sha: str) -> dict:
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"{sha}.json")

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"No scan report found for commit {sha}")

    return json.loads(blob.download_as_text())

@router.get("/api/scans/latest")
async def get_latest_scan():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = sorted(
        client.list_blobs(bucket),
        key=lambda b: b.time_created,
        reverse=True
    )
    if not blobs:
        raise HTTPException(status_code=404, detail="No scan reports found")

    return json.loads(blobs[0].download_as_text())

@router.get("/api/scans/{sha}")
async def get_scan(sha: str):
    return get_scan_report(sha)
