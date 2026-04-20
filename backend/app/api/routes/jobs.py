import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.schemas.dataset import CreateJobRequest, DatasetSourceType
from app.schemas.job import CreateJobResponse, ErrorResponse, JobRecord, JobResponse
from app.services.job_orchestrator import run_job
from app.stores.job_store import job_store

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)


@router.post(
    "/create",
    response_model=CreateJobResponse,
    responses={
        400: {"model": ErrorResponse},
        501: {"model": ErrorResponse},
    },
)
def create_job(payload: CreateJobRequest, background_tasks: BackgroundTasks) -> CreateJobResponse:
    if payload.source_type == DatasetSourceType.CSV_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="CSV upload mode is reserved for the next step and is not implemented yet.",
        )

    if payload.source_type != DatasetSourceType.KAGGLE or payload.kaggle is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kaggle mode requires source_type='kaggle' with a kaggle.competition value.",
        )

    dataset_id = (payload.dataset_id or "").strip() or None
    job = job_store.create(JobRecord())
    background_tasks.add_task(run_job, job.job_id, payload.kaggle, dataset_id)
    logger.info(
        "Created job %s for Kaggle competition '%s' (dataset_id=%s)",
        job.job_id,
        payload.kaggle.competition,
        dataset_id,
    )

    return CreateJobResponse(job_id=job.job_id, status=job.status)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_job(job_id: str) -> JobResponse:
    job = job_store.get(job_id)
    if job is None:
        logger.warning("Requested unknown job id: %s", job_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobResponse(**job.model_dump())
