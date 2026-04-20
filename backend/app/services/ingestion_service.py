import asyncio
import csv
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from app.clients.kaggle_client import KaggleClient
from app.core.config import settings
from app.schemas.dataset import KaggleDatasetInput
from app.utils.file_utils import ensure_dir, extract_zip_archive, find_csv_files, select_primary_csv

_LOCKS_GUARD = threading.Lock()
_COMPETITION_CACHE_LOCKS: dict[str, threading.Lock] = {}


def _safe_competition_name(raw_name: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw_name.strip())


def _build_job_run_dir(competition: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}_{uuid4().hex[:8]}"
    return settings.dataset_storage_root / _safe_competition_name(competition) / run_id


def _build_raw_cache_dirs(competition: str) -> tuple[Path, Path]:
    cache_root = settings.dataset_storage_root / _safe_competition_name(competition) / "raw_cache"
    return cache_root / "download", cache_root / "extracted"


def _find_cached_zip(download_dir: Path, competition: str) -> Path | None:
    expected_zip = download_dir / f"{competition}.zip"
    if expected_zip.exists():
        return expected_zip

    zip_files = sorted(download_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    if zip_files:
        return zip_files[0]

    return None


def _get_competition_lock(competition: str) -> threading.Lock:
    key = _safe_competition_name(competition)
    with _LOCKS_GUARD:
        lock = _COMPETITION_CACHE_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _COMPETITION_CACHE_LOCKS[key] = lock
        return lock


def _ensure_cached_competition_data(dataset: KaggleDatasetInput) -> dict:
    competition_lock = _get_competition_lock(dataset.competition)
    with competition_lock:
        download_dir, extracted_dir = _build_raw_cache_dirs(dataset.competition)
        ensure_dir(download_dir)
        ensure_dir(extracted_dir)

        cached_csv_files = find_csv_files(extracted_dir)
        cached_primary = select_primary_csv(cached_csv_files)
        if cached_primary is not None:
            return {
                "selected_csv": cached_primary,
                "zip_path": _find_cached_zip(download_dir, dataset.competition),
                "extract_path": extracted_dir,
                "csv_files": cached_csv_files,
                "csv_file_count": len(cached_csv_files),
                "download_performed": False,
                "cache_hit": True,
            }

        zip_path = _find_cached_zip(download_dir, dataset.competition)
        download_performed = False
        if zip_path is None:
            kaggle_client = KaggleClient(
                username=settings.kaggle_username,
                key=settings.kaggle_key,
                api_token=settings.kaggle_api_token,
            )
            zip_path = kaggle_client.download_competition_zip(dataset.competition, download_dir)
            download_performed = True

        extract_zip_archive(zip_path=zip_path, destination=extracted_dir)
        extracted_csv_files = find_csv_files(extracted_dir)
        selected_csv = select_primary_csv(extracted_csv_files)
        if selected_csv is None:
            raise RuntimeError(
                f"No CSV files were found after extracting competition '{dataset.competition}'."
            )

        return {
            "selected_csv": selected_csv,
            "zip_path": zip_path,
            "extract_path": extracted_dir,
            "csv_files": extracted_csv_files,
            "csv_file_count": len(extracted_csv_files),
            "download_performed": download_performed,
            "cache_hit": False,
        }


def _build_source_metadata(csv_files: list[Path], selected_csv: Path) -> dict:
    file_names = sorted({csv_file.name for csv_file in csv_files})
    lowered = {name.lower(): name for name in file_names}

    selected_train = lowered.get("train.csv", selected_csv.name)
    selected_test = lowered.get("test.csv")
    sample_submission = lowered.get("sample_submission.csv") or lowered.get("gender_submission.csv")
    if sample_submission is None:
        for name in file_names:
            if "submission" in name.lower():
                sample_submission = name
                break

    file_columns: dict[str, list[str]] = {}
    for csv_file in csv_files:
        try:
            delimiter = _detect_delimiter(csv_file)
            header_df = pd.read_csv(csv_file, sep=delimiter, nrows=0, low_memory=False)
            file_columns[csv_file.name] = [str(column) for column in header_df.columns]
        except Exception:
            file_columns[csv_file.name] = []

    return {
        "files_detected": file_names,
        "selected_train_file": selected_train,
        "selected_test_file": selected_test,
        "sample_submission_file": sample_submission,
        "file_columns": file_columns,
    }


def _simulate_ingestion(dataset: KaggleDatasetInput) -> dict:
    return {
        "source": "kaggle",
        "competition": dataset.competition,
        "selected_file": "train.csv",
        "source_metadata": {
            "files_detected": ["train.csv", "test.csv", "sample_submission.csv"],
            "selected_train_file": "train.csv",
            "selected_test_file": "test.csv",
            "sample_submission_file": "sample_submission.csv",
            "file_columns": {},
        },
        "dataset_metadata": {
            "row_count": 1000,
            "column_count": 12,
            "column_names": [
                "feature_1",
                "feature_2",
                "feature_3",
                "feature_4",
                "feature_5",
            ],
            "delimiter": ",",
        },
        "note": (
            "Simulated ingestion (real Kaggle download is disabled). "
            "Set ENABLE_REAL_KAGGLE_INGESTION=true and provide Kaggle credentials to enable."
        ),
    }


def _detect_delimiter(csv_path: Path) -> str:
    sample = csv_path.read_text(encoding="utf-8", errors="replace")[:8192]
    if not sample.strip():
        return ","

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except csv.Error:
        return ","


def _collect_dataset_metadata(csv_path: Path) -> dict:
    delimiter = _detect_delimiter(csv_path)
    row_count = 0
    column_names: list[str] = []

    try:
        reader = pd.read_csv(csv_path, sep=delimiter, chunksize=100000, low_memory=False)
        for chunk in reader:
            if not column_names:
                column_names = [str(column) for column in chunk.columns]
            row_count += len(chunk)
    except pd.errors.EmptyDataError:
        column_names = []
        row_count = 0
    except Exception as exc:
        raise RuntimeError(
            f"Failed reading selected CSV '{csv_path.name}' for metadata extraction."
        ) from exc

    return {
        "row_count": row_count,
        "column_count": len(column_names),
        "column_names": column_names,
        "delimiter": delimiter,
    }


def _run_real_ingestion(dataset: KaggleDatasetInput) -> dict:
    has_access_token = bool(settings.kaggle_api_token)
    has_legacy_keypair = bool(settings.kaggle_username and settings.kaggle_key)
    if not has_access_token and not has_legacy_keypair:
        raise RuntimeError(
            "Kaggle credentials are missing. Set KAGGLE_API_TOKEN or KAGGLE_USERNAME and KAGGLE_KEY."
        )

    run_dir = ensure_dir(_build_job_run_dir(dataset.competition))
    cache_details = _ensure_cached_competition_data(dataset)
    selected_csv = cache_details["selected_csv"]
    csv_files = cache_details.get("csv_files", [selected_csv])
    dataset_metadata = _collect_dataset_metadata(selected_csv)
    source_metadata = _build_source_metadata(csv_files=csv_files, selected_csv=selected_csv)

    if cache_details["download_performed"]:
        note = "Real Kaggle ingestion completed (downloaded raw data and created cache)."
    elif cache_details["cache_hit"]:
        note = "Real Kaggle ingestion completed (reused cached raw data)."
    else:
        note = "Real Kaggle ingestion completed (reused cached archive, then extracted raw data)."

    return {
        "source": "kaggle",
        "competition": dataset.competition,
        "selected_file": selected_csv.name,
        "selected_file_path": str(selected_csv),
        "zip_path": str(cache_details["zip_path"]) if cache_details["zip_path"] is not None else None,
        "extract_path": str(cache_details["extract_path"]),
        "csv_file_count": int(cache_details["csv_file_count"]),
        "analysis_output_dir": str(run_dir),
        "download_performed": bool(cache_details["download_performed"]),
        "cache_hit": bool(cache_details["cache_hit"]),
        "source_metadata": source_metadata,
        "dataset_metadata": dataset_metadata,
        "note": note,
    }


async def run_ingestion(dataset: KaggleDatasetInput) -> dict:
    if not settings.enable_real_kaggle_ingestion:
        return _simulate_ingestion(dataset)

    return await asyncio.to_thread(_run_real_ingestion, dataset)
