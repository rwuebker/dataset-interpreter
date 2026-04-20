import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    simulate_stage_delay_seconds: float
    simulate_job_failure_probability: float
    dataset_storage_root: Path
    artifact_storage_root: Path
    enable_real_kaggle_ingestion: bool
    enable_real_ai_interpretation: bool
    enable_cleaning_output: bool
    kaggle_username: str | None
    kaggle_key: str | None
    kaggle_api_token: str | None
    openai_api_key: str | None
    openai_model: str


settings = Settings(
    simulate_stage_delay_seconds=float(os.getenv("SIMULATE_STAGE_DELAY_SECONDS", "0.6")),
    simulate_job_failure_probability=float(os.getenv("SIMULATE_JOB_FAILURE_PROBABILITY", "0.0")),
    dataset_storage_root=Path(os.getenv("DATASET_STORAGE_ROOT", "data/raw")).resolve(),
    artifact_storage_root=Path(os.getenv("ARTIFACT_STORAGE_ROOT", "data/artifacts")).resolve(),
    enable_real_kaggle_ingestion=_as_bool(os.getenv("ENABLE_REAL_KAGGLE_INGESTION"), default=False),
    enable_real_ai_interpretation=_as_bool(os.getenv("ENABLE_REAL_AI_INTERPRETATION"), default=True),
    enable_cleaning_output=_as_bool(os.getenv("ENABLE_CLEANING_OUTPUT"), default=False),
    kaggle_username=os.getenv("KAGGLE_USERNAME"),
    kaggle_key=os.getenv("KAGGLE_KEY"),
    kaggle_api_token=os.getenv("KAGGLE_API_TOKEN"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
)
