import asyncio
import logging
import random
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.dataset import KaggleDatasetInput
from app.schemas.job import JobStage, JobStatus
from app.services.ai_interpretation_service import run_ai_interpretation
from app.services.artifact_service import create_artifact_package
from app.services.cleaning_service import run_optional_cleaning
from app.services.ingestion_service import run_ingestion
from app.services.issue_detection_service import run_issue_detection
from app.services.profiling_service import run_profiling
from app.services.summary_service import build_job_summary
from app.stores.job_store import job_store


_STAGE_PROGRESS = {
    JobStage.INGESTION: 25,
    JobStage.PROFILING: 50,
    JobStage.ISSUE_DETECTION: 75,
    JobStage.INTERPRETATION: 90,
}
logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _maybe_simulate_failure(stage: JobStage) -> None:
    if settings.simulate_job_failure_probability <= 0:
        return

    if random.random() < settings.simulate_job_failure_probability:
        logger.warning("Simulating failure at stage '%s'", stage.value)
        raise RuntimeError(f"Simulated failure at stage '{stage.value}'.")


async def run_job(job_id: str, kaggle_input: KaggleDatasetInput) -> None:
    stage_history: list[dict] = []

    def mark_stage_started(stage: JobStage) -> None:
        logger.info("Job %s stage started: %s", job_id, stage.value)
        stage_history.append({"stage": stage.value, "status": "started", "timestamp": _utc_now_iso()})
        job_store.update(
            job_id,
            current_stage=stage,
            progress=_STAGE_PROGRESS[stage],
        )

    def mark_stage_completed(stage: JobStage) -> None:
        logger.info("Job %s stage completed: %s", job_id, stage.value)
        stage_history.append({"stage": stage.value, "status": "completed", "timestamp": _utc_now_iso()})

    try:
        logger.info("Job %s started for competition '%s'", job_id, kaggle_input.competition)
        job_store.update(
            job_id,
            status=JobStatus.RUNNING,
        )
        mark_stage_started(JobStage.INGESTION)
        _maybe_simulate_failure(JobStage.INGESTION)
        ingestion_output = await run_ingestion(kaggle_input)
        mark_stage_completed(JobStage.INGESTION)

        await asyncio.sleep(settings.simulate_stage_delay_seconds)
        mark_stage_started(JobStage.PROFILING)
        _maybe_simulate_failure(JobStage.PROFILING)
        profile_output = await run_profiling(ingestion_output)
        mark_stage_completed(JobStage.PROFILING)

        await asyncio.sleep(settings.simulate_stage_delay_seconds)
        mark_stage_started(JobStage.ISSUE_DETECTION)
        _maybe_simulate_failure(JobStage.ISSUE_DETECTION)
        issues_output = await run_issue_detection(profile_output, ingestion_output)
        mark_stage_completed(JobStage.ISSUE_DETECTION)

        await asyncio.sleep(settings.simulate_stage_delay_seconds)
        mark_stage_started(JobStage.INTERPRETATION)
        _maybe_simulate_failure(JobStage.INTERPRETATION)
        interpretation_output = await run_ai_interpretation(profile_output, issues_output)
        mark_stage_completed(JobStage.INTERPRETATION)

        cleaning_output = {"status": "skipped", "reason": "Cleaning output disabled."}
        if settings.enable_cleaning_output:
            cleaning_output = await asyncio.to_thread(run_optional_cleaning, ingestion_output)

        job_record = job_store.get(job_id)
        artifact_package = await asyncio.to_thread(
            create_artifact_package,
            job_id=job_id,
            created_at=job_record.created_at if job_record is not None else datetime.now(timezone.utc),
            status="completed",
            ingestion_output=ingestion_output,
            profile_output=profile_output,
            issues_output=issues_output,
            interpretation_output=interpretation_output,
            cleaning_output=cleaning_output,
        )

        completed_result = {
            "dataset_profile": profile_output,
            "detected_issues": issues_output,
            "ai_interpretation": interpretation_output,
            "modeling_contract": artifact_package.get("modeling_contract"),
            "cleaned_dataset": artifact_package.get("cleaned_dataset_public"),
            "artifact_manifest": artifact_package.get("manifest"),
            "pipeline_summary": {
                "source": ingestion_output.get("source"),
                "competition": ingestion_output.get("competition"),
                "selected_file": ingestion_output.get("selected_file"),
                "status": "completed",
                "stage_history": stage_history,
            },
        }
        completed_summary = build_job_summary(
            {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "result": completed_result,
            },
            artifact_package.get("manifest"),
        )
        completed_result["summary"] = completed_summary

        job_store.update(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            result=completed_result,
        )
        logger.info("Job %s completed successfully", job_id)
    except Exception as exc:  # pragma: no cover - protective fallback for background tasks
        logger.exception("Job %s failed: %s", job_id, exc)
        stage_history.append({"stage": "job", "status": "failed", "timestamp": _utc_now_iso()})
        job_store.update(
            job_id,
            status=JobStatus.FAILED,
            error=str(exc),
            result={"pipeline_summary": {"status": "failed", "stage_history": stage_history}},
        )
