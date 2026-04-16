import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.clients.kaggle_client import KaggleClient
from app.core.config import settings
from app.schemas.dataset import KaggleDatasetInput
from app.utils.file_utils import ensure_dir, extract_zip_archive, find_csv_files, select_primary_csv


def _safe_competition_name(raw_name: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw_name.strip())


def _build_run_dir(competition: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}_{uuid4().hex[:8]}"
    return settings.dataset_storage_root / _safe_competition_name(competition) / run_id


def _simulate_ingestion(dataset: KaggleDatasetInput) -> dict:
    return {
        "source": "kaggle",
        "competition": dataset.competition,
        "selected_file": "train.csv",
        "note": (
            "Simulated ingestion (real Kaggle download is disabled). "
            "Set ENABLE_REAL_KAGGLE_INGESTION=true and provide Kaggle credentials to enable."
        ),
    }


def _run_real_ingestion(dataset: KaggleDatasetInput) -> dict:
    if not settings.kaggle_username or not settings.kaggle_key:
        raise RuntimeError("Kaggle credentials are missing. Set KAGGLE_USERNAME and KAGGLE_KEY.")

    run_dir = ensure_dir(_build_run_dir(dataset.competition))
    download_dir = ensure_dir(run_dir / "download")
    extracted_dir = run_dir / "extracted"

    kaggle_client = KaggleClient(username=settings.kaggle_username, key=settings.kaggle_key)
    zip_path = kaggle_client.download_competition_zip(dataset.competition, download_dir)
    extract_zip_archive(zip_path=zip_path, destination=extracted_dir)

    csv_files = find_csv_files(extracted_dir)
    selected_csv = select_primary_csv(csv_files)
    if selected_csv is None:
        raise RuntimeError(
            f"No CSV files were found after extracting competition '{dataset.competition}'."
        )

    return {
        "source": "kaggle",
        "competition": dataset.competition,
        "selected_file": selected_csv.name,
        "selected_file_path": str(selected_csv),
        "zip_path": str(zip_path),
        "extract_path": str(extracted_dir),
        "csv_file_count": len(csv_files),
        "note": "Real Kaggle ingestion completed.",
    }


async def run_ingestion(dataset: KaggleDatasetInput) -> dict:
    if not settings.enable_real_kaggle_ingestion:
        return _simulate_ingestion(dataset)

    return await asyncio.to_thread(_run_real_ingestion, dataset)
