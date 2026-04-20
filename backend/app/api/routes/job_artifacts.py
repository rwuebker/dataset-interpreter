import json
import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

from app.schemas.artifact import ArtifactManifestResponse, JobSummaryResponse
from app.schemas.job import ErrorResponse, JobStatus
from app.services.artifact_service import load_manifest, resolve_artifact
from app.services.summary_service import build_job_summary
from app.stores.job_store import job_store

router = APIRouter(prefix="/jobs", tags=["job_artifacts"])
logger = logging.getLogger(__name__)


@router.get(
    "/{job_id}/summary",
    response_model=JobSummaryResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_job_summary(job_id: str) -> JobSummaryResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    manifest = load_manifest(job_id)
    summary = build_job_summary(job.model_dump(), manifest)
    return JobSummaryResponse(**summary)


@router.get(
    "/{job_id}/artifacts",
    response_model=ArtifactManifestResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def get_job_artifacts(job_id: str) -> ArtifactManifestResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Artifacts are only available after job completion.",
        )

    manifest = load_manifest(job_id)
    if manifest is None:
        logger.warning("Missing manifest for completed job %s", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifacts not found for job")
    return ArtifactManifestResponse(**manifest)


@router.get(
    "/{job_id}/artifacts/{artifact_id}",
    responses={
        404: {"model": ErrorResponse},
    },
)
def get_job_artifact(job_id: str, artifact_id: str):
    resolved = resolve_artifact(job_id, artifact_id)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    artifact, artifact_path = resolved
    content_type = str(artifact.get("content_type", "application/octet-stream"))

    if content_type == "application/json":
        with artifact_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return JSONResponse(payload)

    return FileResponse(
        path=str(artifact_path),
        media_type=content_type,
        filename=str(artifact.get("filename", artifact_path.name)),
    )
