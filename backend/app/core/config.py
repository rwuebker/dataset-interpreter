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
    enable_real_kaggle_ingestion: bool
    kaggle_username: str | None
    kaggle_key: str | None


settings = Settings(
    simulate_stage_delay_seconds=float(os.getenv("SIMULATE_STAGE_DELAY_SECONDS", "0.6")),
    simulate_job_failure_probability=float(os.getenv("SIMULATE_JOB_FAILURE_PROBABILITY", "0.0")),
    dataset_storage_root=Path(os.getenv("DATASET_STORAGE_ROOT", "data/raw")).resolve(),
    enable_real_kaggle_ingestion=_as_bool(os.getenv("ENABLE_REAL_KAGGLE_INGESTION"), default=False),
    kaggle_username=os.getenv("KAGGLE_USERNAME"),
    kaggle_key=os.getenv("KAGGLE_KEY"),
)
