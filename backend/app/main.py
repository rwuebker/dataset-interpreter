from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.logging import configure_logging

app = FastAPI(title="Dataset Interpreter", version="0.1.0")
configure_logging()

app.include_router(health_router)
app.include_router(jobs_router)
