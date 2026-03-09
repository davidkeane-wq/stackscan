from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers.pipelines import router as pipelines_router
from routers.scans import router as scans_router

app = FastAPI(title="StackScan Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(pipelines_router)
app.include_router(scans_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve the standalone scan detail page before the catch-all static mount.
@app.get("/scans/{scan_id}", include_in_schema=False)
async def scan_page(scan_id: str):
    return FileResponse("../frontend/scan.html")


# Catch-all: serve the frontend for all other paths.
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
