from pathlib import Path

import pandas as pd

from app.utils.file_utils import ensure_dir


def _safe_indicator_name(column_name: str, existing_columns: set[str]) -> str:
    base = "has_" + "".join(char if char.isalnum() else "_" for char in column_name.strip().lower())
    candidate = base
    suffix = 1
    while candidate in existing_columns:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


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
    derived_columns: list[str] = []
    dropped_columns: list[str] = []
    for column_name in list(df.columns):
        if column_name not in df.columns:
            continue
        if not df[column_name].isna().any():
            continue

        missing_percent = float(df[column_name].isna().mean() * 100.0)

        if pd.api.types.is_numeric_dtype(df[column_name]):
            replacement = df[column_name].median(skipna=True)
            if pd.isna(replacement):
                replacement = 0
            df[column_name] = df[column_name].fillna(replacement)
            imputed_columns.append(str(column_name))
            continue

        if missing_percent >= 60.0:
            indicator_name = _safe_indicator_name(str(column_name), set(str(col) for col in df.columns))
            df[indicator_name] = (~df[column_name].isna()).astype(int)
            derived_columns.append(str(indicator_name))
            df = df.drop(columns=[column_name])
            dropped_columns.append(str(column_name))
            continue

        mode = df[column_name].mode(dropna=True)
        replacement = mode.iloc[0] if not mode.empty else "missing"
        df[column_name] = df[column_name].fillna(replacement)
        imputed_columns.append(str(column_name))

    duplicate_rows_removed = int(df.duplicated().sum())
    df_cleaned = df.drop_duplicates().reset_index(drop=True)
    rows_after = int(df_cleaned.shape[0])

    analysis_output_dir = ingestion_output.get("analysis_output_dir")
    if analysis_output_dir:
        run_dir = ensure_dir(Path(str(analysis_output_dir)))
    else:
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
        "derived_columns": derived_columns,
        "dropped_columns": dropped_columns,
        "type_fixed_columns": type_fixed_columns,
    }
