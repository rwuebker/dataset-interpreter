from datetime import datetime

from pydantic import BaseModel

from app.schemas.job import JobStatus


class ArtifactRecord(BaseModel):
    artifact_id: str
    filename: str
    content_type: str
    description: str
    schema_version: str | None = None
    download_url: str
    created_at: datetime


class ArtifactManifestResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    artifacts: list[ArtifactRecord]


class SummaryTopIssue(BaseModel):
    issue_type: str
    severity: str


class SummaryArtifactLink(BaseModel):
    artifact_id: str
    filename: str
    content_type: str
    download_url: str


class JobSummaryResponse(BaseModel):
    job_id: str
    status: JobStatus
    source: str | None = None
    competition: str | None = None
    dataset_id: str | None = None
    selected_file: str | None = None
    rows: int | None = None
    columns: int | None = None
    inferred_problem_type: str = "unknown"
    inferred_target_column: str | None = None
    target_confidence: float | None = None
    readiness_label: str | None = None
    readiness_score: int | None = None
    top_issues: list[SummaryTopIssue]
    recommended_next_steps: list[str]
    artifacts: list[SummaryArtifactLink]
