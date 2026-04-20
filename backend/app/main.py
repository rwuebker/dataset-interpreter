from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.job_artifacts import router as job_artifacts_router
from app.api.routes.jobs import router as jobs_router
from app.core.logging import configure_logging

app = FastAPI(title="Dataset Interpreter", version="0.1.0")
configure_logging()

# Local demo frontend runs from a separate localhost port.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(job_artifacts_router)
