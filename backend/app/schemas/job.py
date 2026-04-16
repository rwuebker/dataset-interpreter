from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStage(str, Enum):
    INGESTION = "ingestion"
    PROFILING = "profiling"
    ISSUE_DETECTION = "issue_detection"
    INTERPRETATION = "interpretation"


class JobRecord(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.PENDING
    current_stage: JobStage | None = None
    progress: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    current_stage: JobStage | None
    progress: int
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class ErrorResponse(BaseModel):
    detail: str
