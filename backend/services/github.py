import os
import httpx

GITHUB_API_BASE = "https://api.github.com"


def _auth_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def get_workflow_runs(owner: str, repo: str, per_page: int = 30) -> dict:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs"
    params = {"per_page": per_page}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = client.build_request("GET", url, params=params, headers=_auth_headers())
        r = await client.send(response)
        r.raise_for_status()
        return r.json()
