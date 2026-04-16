import asyncio

from app.core.config import settings
from app.schemas.dataset import KaggleDatasetInput
from app.schemas.job import JobStage, JobStatus
from app.services.ai_interpretation_service import run_ai_interpretation
from app.services.ingestion_service import run_ingestion
from app.services.issue_detection_service import run_issue_detection
from app.services.profiling_service import run_profiling
from app.stores.job_store import job_store


_STAGE_PROGRESS = {
    JobStage.INGESTION: 25,
    JobStage.PROFILING: 50,
    JobStage.ISSUE_DETECTION: 75,
    JobStage.INTERPRETATION: 90,
}


async def run_job(job_id: str, kaggle_input: KaggleDatasetInput) -> None:
    job_store.update(
        job_id,
        status=JobStatus.RUNNING,
        current_stage=JobStage.INGESTION,
        progress=_STAGE_PROGRESS[JobStage.INGESTION],
    )
    await asyncio.sleep(settings.simulate_stage_delay_seconds)
    ingestion_output = await run_ingestion(kaggle_input)

    job_store.update(
        job_id,
        current_stage=JobStage.PROFILING,
        progress=_STAGE_PROGRESS[JobStage.PROFILING],
    )
    await asyncio.sleep(settings.simulate_stage_delay_seconds)
    profile_output = await run_profiling(ingestion_output)

    job_store.update(
        job_id,
        current_stage=JobStage.ISSUE_DETECTION,
        progress=_STAGE_PROGRESS[JobStage.ISSUE_DETECTION],
    )
    await asyncio.sleep(settings.simulate_stage_delay_seconds)
    issues_output = await run_issue_detection(profile_output)

    job_store.update(
        job_id,
        current_stage=JobStage.INTERPRETATION,
        progress=_STAGE_PROGRESS[JobStage.INTERPRETATION],
    )
    await asyncio.sleep(settings.simulate_stage_delay_seconds)
    interpretation_output = await run_ai_interpretation(profile_output, issues_output)

    job_store.update(
        job_id,
        status=JobStatus.COMPLETED,
        progress=100,
        result={
            "dataset_profile": profile_output,
            "detected_issues": issues_output,
            "ai_interpretation": interpretation_output,
            "pipeline_summary": {
                "source": ingestion_output.get("source"),
                "competition": ingestion_output.get("competition"),
                "selected_file": ingestion_output.get("selected_file"),
                "status": "completed",
            },
        },
    )
