from pathlib import Path

import pandas as pd

from app.utils.file_utils import ensure_dir


def _coerce_numeric_if_mostly_numeric(series: pd.Series, threshold: float = 0.9) -> pd.Series:
    if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
        return series

    non_null = series.dropna().astype(str).str.strip()
    if non_null.empty:
        return series

    parsed = pd.to_numeric(non_null, errors="coerce")
    ratio_numeric = parsed.notna().mean()
    if ratio_numeric < threshold:
        return series

    converted = pd.to_numeric(series, errors="coerce")
    return converted


def run_optional_cleaning(ingestion_output: dict) -> dict:
    selected_file_path = ingestion_output.get("selected_file_path")
    if not selected_file_path:
        return {
            "status": "skipped",
            "reason": "No selected_file_path available for cleaning.",
        }

    selected_csv = Path(selected_file_path)
    if not selected_csv.exists():
        return {
            "status": "skipped",
            "reason": f"Selected CSV path does not exist: {selected_csv}",
        }

    delimiter = ingestion_output.get("dataset_metadata", {}).get("delimiter", ",")
    df = pd.read_csv(selected_csv, sep=delimiter, low_memory=False)
    rows_before = int(df.shape[0])

    type_fixed_columns: list[str] = []
    for column_name in df.columns:
        converted = _coerce_numeric_if_mostly_numeric(df[column_name])
        if not converted.equals(df[column_name]):
            type_fixed_columns.append(str(column_name))
            df[column_name] = converted

    imputed_columns: list[str] = []
    for column_name in df.columns:
        if not df[column_name].isna().any():
            continue

        if pd.api.types.is_numeric_dtype(df[column_name]):
            replacement = df[column_name].median(skipna=True)
            if pd.isna(replacement):
                replacement = 0
            df[column_name] = df[column_name].fillna(replacement)
        else:
            mode = df[column_name].mode(dropna=True)
            replacement = mode.iloc[0] if not mode.empty else "missing"
            df[column_name] = df[column_name].fillna(replacement)
        imputed_columns.append(str(column_name))

    duplicate_rows_removed = int(df.duplicated().sum())
    df_cleaned = df.drop_duplicates().reset_index(drop=True)
    rows_after = int(df_cleaned.shape[0])

    run_dir = selected_csv.parent.parent if len(selected_csv.parents) >= 2 else selected_csv.parent
    cleaned_dir = ensure_dir(run_dir / "cleaned")
    cleaned_file_path = cleaned_dir / f"cleaned_{selected_csv.name}"
    df_cleaned.to_csv(cleaned_file_path, index=False)

    return {
        "status": "completed",
        "cleaned_file_path": str(cleaned_file_path),
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "duplicate_rows_removed": duplicate_rows_removed,
        "imputed_columns": imputed_columns,
        "type_fixed_columns": type_fixed_columns,
    }
