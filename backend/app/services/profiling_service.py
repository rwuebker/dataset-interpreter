import asyncio
from pathlib import Path

import pandas as pd


def _classify_columns(df: pd.DataFrame) -> dict:
    numerical_columns: list[str] = []
    categorical_columns: list[str] = []
    boolean_columns: list[str] = []

    for column_name in df.columns:
        series = df[column_name]
        if pd.api.types.is_bool_dtype(series):
            boolean_columns.append(str(column_name))
        elif pd.api.types.is_numeric_dtype(series):
            numerical_columns.append(str(column_name))
        else:
            categorical_columns.append(str(column_name))

    return {
        "numerical": numerical_columns,
        "categorical": categorical_columns,
        "boolean": boolean_columns,
    }


def _build_missing_values(df: pd.DataFrame) -> dict:
    total_cells = int(df.shape[0] * df.shape[1])
    total_missing = int(df.isna().sum().sum())
    missing_percent = round((total_missing / total_cells) * 100, 4) if total_cells else 0.0

    by_column = []
    for column_name in df.columns:
        missing_count = int(df[column_name].isna().sum())
        column_missing_percent = round((missing_count / len(df)) * 100, 4) if len(df) else 0.0
        by_column.append(
            {
                "column": str(column_name),
                "missing_count": missing_count,
                "missing_percent": column_missing_percent,
            }
        )

    return {
        "total_missing": total_missing,
        "total_cells": total_cells,
        "missing_percent": missing_percent,
        "by_column": by_column,
    }


def _build_numeric_summary(df: pd.DataFrame) -> dict:
    summary: dict[str, dict] = {}
    numeric_df = df.select_dtypes(include=["number"])

    for column_name in numeric_df.columns:
        series = numeric_df[column_name]
        summary[str(column_name)] = {
            "min": None if series.empty else float(series.min(skipna=True)) if series.notna().any() else None,
            "max": None if series.empty else float(series.max(skipna=True)) if series.notna().any() else None,
            "mean": None if series.empty else float(series.mean(skipna=True)) if series.notna().any() else None,
            "median": None if series.empty else float(series.median(skipna=True)) if series.notna().any() else None,
        }

    return summary


def _simulate_profile_from_ingestion(ingestion_output: dict) -> dict:
    metadata = ingestion_output.get("dataset_metadata", {})
    column_names = metadata.get("column_names", [])
    row_count = int(metadata.get("row_count", 1000))
    column_count = int(metadata.get("column_count", len(column_names) or 12))

    return {
        "rows": row_count,
        "columns": column_count,
        "column_names": column_names,
        "column_types": {
            "numerical": [],
            "categorical": column_names,
            "boolean": [],
        },
        "missing_values": {
            "total_missing": 0,
            "total_cells": row_count * column_count,
            "missing_percent": 0.0,
            "by_column": [
                {"column": column_name, "missing_count": 0, "missing_percent": 0.0}
                for column_name in column_names
            ],
        },
        "numeric_summary": {},
        "note": "Simulated profiling (selected_file_path unavailable).",
        "ingestion_ref": ingestion_output.get("selected_file"),
    }


def _run_real_profiling(ingestion_output: dict) -> dict:
    selected_file_path = ingestion_output.get("selected_file_path")
    if not selected_file_path:
        return _simulate_profile_from_ingestion(ingestion_output)

    selected_csv_path = Path(selected_file_path)
    if not selected_csv_path.exists():
        raise RuntimeError(
            f"Selected CSV path does not exist for profiling: {selected_csv_path}"
        )

    delimiter = ingestion_output.get("dataset_metadata", {}).get("delimiter", ",")
    try:
        df = pd.read_csv(selected_csv_path, sep=delimiter, low_memory=False)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to profile selected CSV '{selected_csv_path.name}'."
        ) from exc

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": [str(column) for column in df.columns],
        "column_types": _classify_columns(df),
        "missing_values": _build_missing_values(df),
        "numeric_summary": _build_numeric_summary(df),
        "note": "Profile generated from selected CSV.",
        "ingestion_ref": ingestion_output.get("selected_file"),
    }


async def run_profiling(ingestion_output: dict) -> dict:
    return await asyncio.to_thread(_run_real_profiling, ingestion_output)
