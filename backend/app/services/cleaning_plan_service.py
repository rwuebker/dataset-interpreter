from __future__ import annotations

from datetime import datetime, timezone


CLEANING_PLAN_SCHEMA_VERSION = "dataset_interpreter.cleaning_plan.v1"
CLEANING_RECEIPT_SCHEMA_VERSION = "dataset_interpreter.cleaning_receipt.v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_cleaning_plan(
    *,
    job_id: str,
    ingestion_output: dict,
    modeling_contract: dict,
) -> dict:
    recommended_steps = modeling_contract.get("recommended_preprocessing", [])
    return {
        "schema_version": CLEANING_PLAN_SCHEMA_VERSION,
        "job_id": job_id,
        "source": ingestion_output.get("source"),
        "competition": ingestion_output.get("competition"),
        "selected_file": ingestion_output.get("selected_file"),
        "readiness_label": modeling_contract.get("dataset", {}).get("readiness_label"),
        "quality_gates": modeling_contract.get("quality_gates", {}),
        "recommended_transformations": recommended_steps,
        "note": (
            "Plan is deterministic and recommendation-oriented. "
            "It may include transformations not executed in this run."
        ),
        "created_at": _now_iso(),
    }


def build_cleaning_receipt(
    *,
    job_id: str,
    cleaning_output: dict,
    cleaned_artifact: dict | None = None,
) -> dict:
    if cleaning_output.get("status") != "completed":
        return {
            "schema_version": CLEANING_RECEIPT_SCHEMA_VERSION,
            "job_id": job_id,
            "status": cleaning_output.get("status", "skipped"),
            "reason": cleaning_output.get("reason", "Cleaning not executed."),
            "cleaned_dataset_artifact": None,
            "created_at": _now_iso(),
        }

    return {
        "schema_version": CLEANING_RECEIPT_SCHEMA_VERSION,
        "job_id": job_id,
        "status": "completed",
        "rows_before": int(cleaning_output.get("rows_before", 0)),
        "rows_after": int(cleaning_output.get("rows_after", 0)),
        "rows_removed": int(cleaning_output.get("rows_removed", 0)),
        "duplicate_rows_removed": int(cleaning_output.get("duplicate_rows_removed", 0)),
        "imputed_columns": list(cleaning_output.get("imputed_columns", [])),
        "derived_columns": list(cleaning_output.get("derived_columns", [])),
        "dropped_columns": list(cleaning_output.get("dropped_columns", [])),
        "type_fixed_columns": list(cleaning_output.get("type_fixed_columns", [])),
        "cleaned_dataset_artifact": cleaned_artifact,
        "created_at": _now_iso(),
    }
