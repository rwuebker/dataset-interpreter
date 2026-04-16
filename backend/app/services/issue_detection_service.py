import asyncio
from pathlib import Path

import pandas as pd


def _missing_severity(missing_percent: float) -> str:
    if missing_percent <= 1:
        return "low"
    if missing_percent <= 10:
        return "moderate"
    return "high"


def _ratio_to_severity(ratio: float) -> str:
    if ratio <= 0:
        return "none"
    if ratio <= 0.01:
        return "low"
    if ratio <= 0.05:
        return "moderate"
    return "high"


def _scan_dataset_issues(csv_path: Path, delimiter: str) -> dict:
    try:
        df = pd.read_csv(csv_path, sep=delimiter, low_memory=False)
    except Exception as exc:
        raise RuntimeError(f"Failed scanning dataset for issue detection: {csv_path.name}") from exc

    duplicate_rows = int(df.duplicated().sum())

    outlier_cells = 0
    numeric_df = df.select_dtypes(include=["number"])
    for column_name in numeric_df.columns:
        series = numeric_df[column_name].dropna()
        if len(series) < 4:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)
        outlier_cells += int(((series < lower) | (series > upper)).sum())

    inconsistent_columns: list[str] = []
    object_df = df.select_dtypes(include=["object", "string"])
    for column_name in object_df.columns:
        non_null = object_df[column_name].dropna().astype(str).str.strip()
        if non_null.empty:
            continue
        parsed = pd.to_numeric(non_null, errors="coerce")
        has_numeric_like = parsed.notna().any()
        has_non_numeric = parsed.isna().any()
        if has_numeric_like and has_non_numeric:
            inconsistent_columns.append(str(column_name))

    row_count = max(int(df.shape[0]), 1)
    outlier_denominator = max(row_count * max(len(numeric_df.columns), 1), 1)
    duplicate_ratio = duplicate_rows / row_count
    outlier_ratio = outlier_cells / outlier_denominator

    return {
        "duplicate_rows": duplicate_rows,
        "outlier_cells": outlier_cells,
        "inconsistent_columns": inconsistent_columns,
        "duplicate_ratio": duplicate_ratio,
        "outlier_ratio": outlier_ratio,
    }


def _build_issue_list(
    missing_severity: str,
    duplicate_severity: str,
    outlier_severity: str,
    inconsistent_columns: list[str],
) -> list[dict]:
    issues: list[dict] = []

    if missing_severity in {"moderate", "high"}:
        issues.append(
            {
                "issue_type": "missing_data",
                "severity": missing_severity,
                "recommended_action": "Define column-level imputation and null-handling strategy.",
            }
        )

    if duplicate_severity != "none":
        issues.append(
            {
                "issue_type": "duplicates",
                "severity": duplicate_severity,
                "recommended_action": "Deduplicate rows before train/validation split.",
            }
        )

    if outlier_severity != "none":
        issues.append(
            {
                "issue_type": "outliers",
                "severity": outlier_severity,
                "recommended_action": "Review outlier-heavy columns and consider robust scaling or capping.",
            }
        )

    if inconsistent_columns:
        issues.append(
            {
                "issue_type": "type_inconsistencies",
                "severity": "moderate",
                "recommended_action": "Normalize mixed-type columns before feature engineering.",
                "affected_columns": inconsistent_columns,
            }
        )

    return issues


def _run_issue_detection(profile_output: dict, ingestion_output: dict | None) -> dict:
    rows = int(profile_output.get("rows", 0))
    missing_percent = float(profile_output.get("missing_values", {}).get("missing_percent", 0.0))
    missing_severity = _missing_severity(missing_percent)

    duplicate_severity = "none"
    outlier_severity = "none"
    duplicate_rows = 0
    outlier_cells = 0
    inconsistent_columns: list[str] = []

    selected_file_path = (ingestion_output or {}).get("selected_file_path")
    if selected_file_path:
        delimiter = (ingestion_output or {}).get("dataset_metadata", {}).get("delimiter", ",")
        scan = _scan_dataset_issues(Path(selected_file_path), delimiter)
        duplicate_rows = scan["duplicate_rows"]
        outlier_cells = scan["outlier_cells"]
        inconsistent_columns = scan["inconsistent_columns"]
        duplicate_severity = _ratio_to_severity(scan["duplicate_ratio"])
        outlier_severity = _ratio_to_severity(scan["outlier_ratio"])

    issues = _build_issue_list(
        missing_severity=missing_severity,
        duplicate_severity=duplicate_severity,
        outlier_severity=outlier_severity,
        inconsistent_columns=inconsistent_columns,
    )

    return {
        "missing_data": missing_severity,
        "duplicates": duplicate_severity,
        "outliers": outlier_severity,
        "type_inconsistencies": "detected" if inconsistent_columns else "none_detected",
        "issues": issues,
        "summary": {
            "duplicate_rows": duplicate_rows,
            "outlier_cells": outlier_cells,
            "inconsistent_columns": inconsistent_columns,
            "rows_analyzed": rows,
        },
        "note": "Issue detection generated from profile output and dataset checks.",
        "profile_rows_ref": rows,
    }


async def run_issue_detection(profile_output: dict, ingestion_output: dict | None = None) -> dict:
    return await asyncio.to_thread(_run_issue_detection, profile_output, ingestion_output)
