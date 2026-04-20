from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.stores.job_store import job_store
from app.services.cleaning_plan_service import (
    CLEANING_PLAN_SCHEMA_VERSION,
    CLEANING_RECEIPT_SCHEMA_VERSION,
    build_cleaning_plan,
    build_cleaning_receipt,
)
from app.services.feature_card_service import FEATURE_CARDS_SCHEMA_VERSION, build_feature_cards
from app.services.modeling_contract_service import MODEL_CONTRACT_SCHEMA_VERSION, build_modeling_contract
from app.utils.file_utils import ensure_dir


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _safe_path_component(raw_value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw_value.strip())


def _competition_artifact_root(competition: str) -> Path:
    safe_competition = _safe_path_component(competition)
    return settings.dataset_storage_root / safe_competition / "_artifacts"


def _artifact_root_for_run(competition: str, dataset_id: str | None) -> Path:
    base = _competition_artifact_root(competition)
    if dataset_id:
        safe_dataset_id = _safe_path_component(dataset_id)
        return base / "by_dataset" / safe_dataset_id
    return base / "current"


def _artifact_mode(dataset_id: str | None) -> str:
    return "dataset_persistent" if dataset_id else "current_overwrite"


def _clear_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def prepare_artifact_workspace(competition: str, dataset_id: str | None) -> Path:
    root = _artifact_root_for_run(competition, dataset_id)
    _clear_directory(root)
    return ensure_dir(root)


def _legacy_artifact_root(job_id: str) -> Path:
    return settings.artifact_storage_root / job_id


def _resolve_job_artifact_root(job_id: str) -> Path | None:
    job = job_store.get(job_id)
    if job is not None:
        result = job.result or {}
        pipeline_summary = result.get("pipeline_summary") or {}
        competition = pipeline_summary.get("competition")
        dataset_id = pipeline_summary.get("dataset_id")
        if competition:
            preferred_path = _artifact_root_for_run(str(competition), str(dataset_id) if dataset_id else None)
            if preferred_path.exists():
                return preferred_path

    legacy_path = _legacy_artifact_root(job_id)
    if legacy_path.exists():
        return legacy_path
    return None


def _manifest_path(job_id: str) -> Path | None:
    root = _resolve_job_artifact_root(job_id)
    if root is None:
        return None
    return root / "manifest.json"


def _download_url(job_id: str, artifact_id: str) -> str:
    return f"/jobs/{job_id}/artifacts/{artifact_id}"


def _write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def _dataset_report(
    *,
    job_id: str,
    ingestion_output: dict,
    profile_output: dict,
    issues_output: dict,
    interpretation_output: dict,
) -> dict:
    return {
        "schema_version": "dataset_interpreter.dataset_report.v1",
        "job_id": job_id,
        "source": ingestion_output.get("source"),
        "competition": ingestion_output.get("competition"),
        "selected_file": ingestion_output.get("selected_file"),
        "rows": profile_output.get("rows"),
        "columns": profile_output.get("columns"),
        "missing_data": issues_output.get("missing_data"),
        "duplicates": issues_output.get("duplicates"),
        "outliers": issues_output.get("outliers"),
        "type_inconsistencies": issues_output.get("type_inconsistencies"),
        "likely_ml_problem": interpretation_output.get("likely_ml_problem"),
        "recommended_next_steps": interpretation_output.get("suggested_next_steps")
        or interpretation_output.get("recommended_next_steps", []),
        "created_at": _utc_now_iso(),
    }


def _public_cleaned_dataset(cleaning_receipt: dict) -> dict:
    if cleaning_receipt.get("status") != "completed":
        return {
            "status": cleaning_receipt.get("status", "skipped"),
            "reason": cleaning_receipt.get("reason"),
        }

    return {
        "status": "completed",
        "rows_before": cleaning_receipt.get("rows_before"),
        "rows_after": cleaning_receipt.get("rows_after"),
        "rows_removed": cleaning_receipt.get("rows_removed"),
        "duplicate_rows_removed": cleaning_receipt.get("duplicate_rows_removed"),
        "imputed_columns": cleaning_receipt.get("imputed_columns", []),
        "derived_columns": cleaning_receipt.get("derived_columns", []),
        "dropped_columns": cleaning_receipt.get("dropped_columns", []),
        "type_fixed_columns": cleaning_receipt.get("type_fixed_columns", []),
        "cleaned_dataset_artifact": cleaning_receipt.get("cleaned_dataset_artifact"),
    }


def create_artifact_package(
    *,
    job_id: str,
    created_at: datetime,
    status: str,
    competition: str,
    dataset_id: str | None,
    ingestion_output: dict,
    profile_output: dict,
    issues_output: dict,
    interpretation_output: dict,
    cleaning_output: dict,
) -> dict:
    artifact_root = _artifact_root_for_run(competition, dataset_id)
    _clear_directory(artifact_root)
    artifact_dir = ensure_dir(artifact_root)
    created_at_iso = _utc_now_iso()
    records: list[dict] = []

    def register(
        *,
        artifact_id: str,
        filename: str,
        content_type: str,
        description: str,
        schema_version: str | None = None,
    ) -> dict:
        record = {
            "artifact_id": artifact_id,
            "filename": filename,
            "content_type": content_type,
            "description": description,
            "schema_version": schema_version,
            "download_url": _download_url(job_id, artifact_id),
            "created_at": created_at_iso,
        }
        records.append(record)
        return record

    base_links = [
        {
            "artifact_id": "dataset_report",
            "download_url": _download_url(job_id, "dataset_report"),
        },
        {
            "artifact_id": "data_profile",
            "download_url": _download_url(job_id, "data_profile"),
        },
        {
            "artifact_id": "issue_report",
            "download_url": _download_url(job_id, "issue_report"),
        },
        {
            "artifact_id": "interpretation",
            "download_url": _download_url(job_id, "interpretation"),
        },
        {
            "artifact_id": "feature_cards",
            "download_url": _download_url(job_id, "feature_cards"),
        },
        {
            "artifact_id": "cleaning_plan",
            "download_url": _download_url(job_id, "cleaning_plan"),
        },
        {
            "artifact_id": "cleaning_receipt",
            "download_url": _download_url(job_id, "cleaning_receipt"),
        },
        {
            "artifact_id": "modeling_contract",
            "download_url": _download_url(job_id, "modeling_contract"),
        },
    ]

    dataset_report = _dataset_report(
        job_id=job_id,
        ingestion_output=ingestion_output,
        profile_output=profile_output,
        issues_output=issues_output,
        interpretation_output=interpretation_output,
    )
    _write_json(artifact_dir / "dataset_report.json", dataset_report)
    register(
        artifact_id="dataset_report",
        filename="dataset_report.json",
        content_type="application/json",
        description="Human-readable dataset overview and recommendations.",
        schema_version="dataset_interpreter.dataset_report.v1",
    )

    _write_json(artifact_dir / "data_profile.json", profile_output)
    register(
        artifact_id="data_profile",
        filename="data_profile.json",
        content_type="application/json",
        description="Structured data profile output.",
        schema_version="dataset_interpreter.data_profile.v1",
    )

    _write_json(artifact_dir / "issue_report.json", issues_output)
    register(
        artifact_id="issue_report",
        filename="issue_report.json",
        content_type="application/json",
        description="Structured issue detection output.",
        schema_version="dataset_interpreter.issue_report.v1",
    )

    _write_json(artifact_dir / "interpretation.json", interpretation_output)
    register(
        artifact_id="interpretation",
        filename="interpretation.json",
        content_type="application/json",
        description="AI interpretation output grounded in computed statistics.",
        schema_version="dataset_interpreter.interpretation.v1",
    )

    modeling_contract = build_modeling_contract(
        job_id=job_id,
        created_at=created_at,
        ingestion_output=ingestion_output,
        profile_output=profile_output,
        issues_output=issues_output,
        artifact_links=base_links,
    )
    _write_json(artifact_dir / "modeling_contract.json", modeling_contract)
    register(
        artifact_id="modeling_contract",
        filename="modeling_contract.json",
        content_type="application/json",
        description="Machine-readable handoff contract for downstream modeling systems.",
        schema_version=MODEL_CONTRACT_SCHEMA_VERSION,
    )

    feature_cards = build_feature_cards(profile_output, issues_output, modeling_contract)
    _write_jsonl(artifact_dir / "feature_cards.jsonl", feature_cards)
    register(
        artifact_id="feature_cards",
        filename="feature_cards.jsonl",
        content_type="application/jsonl",
        description="Per-column deterministic feature cards.",
        schema_version=FEATURE_CARDS_SCHEMA_VERSION,
    )

    cleaning_plan = build_cleaning_plan(
        job_id=job_id,
        ingestion_output=ingestion_output,
        modeling_contract=modeling_contract,
    )
    _write_json(artifact_dir / "cleaning_plan.json", cleaning_plan)
    register(
        artifact_id="cleaning_plan",
        filename="cleaning_plan.json",
        content_type="application/json",
        description="Recommended cleaning and preprocessing plan.",
        schema_version=CLEANING_PLAN_SCHEMA_VERSION,
    )

    cleaned_artifact_ref = None
    cleaned_source_path = cleaning_output.get("cleaned_file_path")
    if cleaning_output.get("status") == "completed" and cleaned_source_path:
        source_file = Path(str(cleaned_source_path))
        if source_file.exists():
            cleaned_filename = "cleaned_train.csv"
            shutil.copy2(source_file, artifact_dir / cleaned_filename)
            cleaned_artifact_ref = {
                "artifact_id": "cleaned_train_csv",
                "filename": cleaned_filename,
                "content_type": "text/csv",
                "download_url": _download_url(job_id, "cleaned_train_csv"),
            }
            register(
                artifact_id="cleaned_train_csv",
                filename=cleaned_filename,
                content_type="text/csv",
                description="Cleaned dataset output generated by cleaning service.",
            )

    cleaning_receipt = build_cleaning_receipt(
        job_id=job_id,
        cleaning_output=cleaning_output,
        cleaned_artifact=cleaned_artifact_ref,
    )
    _write_json(artifact_dir / "cleaning_receipt.json", cleaning_receipt)
    register(
        artifact_id="cleaning_receipt",
        filename="cleaning_receipt.json",
        content_type="application/json",
        description="Receipt describing what cleaning was actually executed.",
        schema_version=CLEANING_RECEIPT_SCHEMA_VERSION,
    )

    manifest = {
        "job_id": job_id,
        "status": status,
        "created_at": created_at_iso,
        "competition": competition,
        "dataset_id": dataset_id,
        "storage_mode": _artifact_mode(dataset_id),
        "artifacts": records
        + [
            {
                "artifact_id": "manifest",
                "filename": "manifest.json",
                "content_type": "application/json",
                "description": "Artifact inventory for this job.",
                "schema_version": "dataset_interpreter.artifact_manifest.v1",
                "download_url": _download_url(job_id, "manifest"),
                "created_at": created_at_iso,
            }
        ],
    }
    _write_json(artifact_dir / "manifest.json", manifest)

    return {
        "manifest": manifest,
        "modeling_contract": modeling_contract,
        "cleaning_receipt": cleaning_receipt,
        "cleaned_dataset_public": _public_cleaned_dataset(cleaning_receipt),
    }


def load_manifest(job_id: str) -> dict | None:
    path = _manifest_path(job_id)
    if path is None or not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("job_id") != job_id:
        return None
    return payload


def resolve_artifact(job_id: str, artifact_id: str) -> tuple[dict, Path] | None:
    manifest = load_manifest(job_id)
    if not manifest:
        return None
    artifact_root = _resolve_job_artifact_root(job_id)
    if artifact_root is None:
        return None

    for artifact in manifest.get("artifacts", []):
        if artifact.get("artifact_id") != artifact_id:
            continue
        artifact_path = artifact_root / str(artifact.get("filename"))
        if artifact_path.exists():
            return artifact, artifact_path
        return None
    return None
