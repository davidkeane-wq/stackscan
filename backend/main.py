from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers.pipelines import router as pipelines_router 
from routers.scans import router as scans_router

app = FastAPI(title="Pipeline Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(pipelines_router)
app.include_router(scans_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")