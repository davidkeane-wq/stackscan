import pytest
import respx
import httpx
from httpx import AsyncClient
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

MOCK_RUNS_RESPONSE = {
    "total_count": 1,
    "workflow_runs": [
        {
            "id": 1,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "head_branch": "main",
            "event": "push",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:05:00Z",
            "html_url": "https://github.com/owner/repo/actions/runs/1",
        }
    ],
}


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@respx.mock
def test_list_pipeline_runs_success():
    respx.get("https://api.github.com/repos/owner/repo/actions/runs").mock(
        return_value=httpx.Response(200, json=MOCK_RUNS_RESPONSE)
    )
    with TestClient(app) as client:
        response = client.get("/api/pipelines/owner/repo")
    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 1
    assert len(body["runs"]) == 1
    run = body["runs"][0]
    assert run["name"] == "CI"
    assert run["status"] == "completed"
    assert run["conclusion"] == "success"
    assert run["branch"] == "main"


@respx.mock
def test_list_pipeline_runs_not_found():
    respx.get("https://api.github.com/repos/owner/missing/actions/runs").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    with TestClient(app) as client:
        response = client.get("/api/pipelines/owner/missing")
    assert response.status_code == 404


@respx.mock
def test_list_pipeline_runs_github_unavailable():
    respx.get("https://api.github.com/repos/owner/repo/actions/runs").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    with TestClient(app) as client:
        response = client.get("/api/pipelines/owner/repo")
    assert response.status_code == 503
