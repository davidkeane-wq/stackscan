from fastapi import APIRouter, HTTPException
import httpx

from services.github import get_workflow_runs

router = APIRouter()


@router.get("/api/pipelines/{owner}/{repo}")
async def list_pipeline_runs(owner: str, repo: str, per_page: int = 30):
    try:
        data = await get_workflow_runs(owner, repo, per_page=per_page)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"GitHub API unreachable: {e}")

    runs = [
        {
            "id": run["id"],
            "name": run["name"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "branch": run["head_branch"],
            "event": run["event"],
            "created_at": run["created_at"],
            "updated_at": run["updated_at"],
            "html_url": run["html_url"],
        }
        for run in data.get("workflow_runs", [])
    ]
    return {"total_count": data.get("total_count", 0), "runs": runs}
