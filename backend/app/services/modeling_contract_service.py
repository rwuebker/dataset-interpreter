from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone


MODEL_CONTRACT_SCHEMA_VERSION = "dataset_interpreter.modeling_contract.v1"


def _to_iso(dt: datetime | None = None) -> str:
    value = dt or datetime.now(timezone.utc)
    return value.isoformat()


def _cardinality_map(profile_output: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in profile_output.get("cardinality", []):
        column = str(item.get("column", ""))
        if not column:
            continue
        result[column] = item
    return result


def _missing_map(profile_output: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    by_column = profile_output.get("missing_values", {}).get("by_column", [])
    for item in by_column:
        column = str(item.get("column", ""))
        if not column:
            continue
        result[column] = item
    return result


def _is_identifier_name(column_name: str) -> bool:
    normalized = column_name.strip().lower()
    return normalized.endswith("id") or normalized.endswith("_id") or normalized in {"id", "passengerid"}


def _ordered_subset(columns: Iterable[str], ordered_source: list[str]) -> list[str]:
    lookup = set(columns)
    return [column for column in ordered_source if column in lookup]


def _infer_target_from_files(
    ingestion_output: dict,
    profile_output: dict,
    cardinality: dict[str, dict],
) -> tuple[str | None, float, str]:
    source_metadata = ingestion_output.get("source_metadata", {})
    file_columns = source_metadata.get("file_columns", {})
    selected_train = source_metadata.get("selected_train_file")
    selected_test = source_metadata.get("selected_test_file")
    sample_submission = source_metadata.get("sample_submission_file")

    if selected_train and selected_test and sample_submission:
        train_columns = set(file_columns.get(selected_train, []))
        test_columns = set(file_columns.get(selected_test, []))
        sample_columns = set(file_columns.get(sample_submission, []))

        candidates = sorted(
            column
            for column in (train_columns & sample_columns) - test_columns
            if not _is_identifier_name(column)
        )
        if len(candidates) == 1:
            return candidates[0], 0.95, "Inferred from train/test/sample_submission column overlap."

        if len(candidates) > 1:
            ranked = sorted(
                candidates,
                key=lambda column: (
                    int(cardinality.get(column, {}).get("unique_count", 10**9)),
                    column,
                ),
            )
            return ranked[0], 0.85, "Inferred from train/test/sample_submission overlap with tie-break on cardinality."

    known_targets = ("target", "label", "survived", "class", "outcome")
    for column in profile_output.get("column_names", []):
        lower_name = str(column).strip().lower()
        if lower_name in known_targets:
            return str(column), 0.70, "Inferred from common target naming pattern."

    binary_candidates = []
    for column, item in cardinality.items():
        unique_count = int(item.get("unique_count", 0))
        if unique_count == 2 and not _is_identifier_name(column):
            binary_candidates.append(column)
    if len(binary_candidates) == 1:
        return binary_candidates[0], 0.55, "Inferred as the only binary non-identifier column."

    return None, 0.0, "Target could not be inferred with current deterministic heuristics."


def _infer_problem_type(
    target_column: str | None,
    profile_output: dict,
    cardinality: dict[str, dict],
) -> tuple[str, str | None]:
    if not target_column:
        return "unknown", None

    column_types = profile_output.get("column_types", {})
    numerical = set(column_types.get("numerical", []))
    categorical = set(column_types.get("categorical", []))
    boolean = set(column_types.get("boolean", []))
    unique_count = int(cardinality.get(target_column, {}).get("unique_count", 0))

    if target_column in boolean or unique_count == 2:
        return "binary_classification", "accuracy"

    if target_column in categorical:
        return "multiclass_classification", "macro_f1"

    if target_column in numerical:
        if unique_count <= 20:
            return "multiclass_classification", "macro_f1"
        return "regression", "rmse"

    return "unknown", None


def _infer_id_columns(
    profile_output: dict,
    cardinality: dict[str, dict],
    target_column: str | None,
) -> list[str]:
    id_candidates: list[str] = []
    for column in profile_output.get("column_names", []):
        column_name = str(column)
        if target_column and column_name == target_column:
            continue
        unique_percent = float(cardinality.get(column_name, {}).get("unique_percent", 0.0))
        if _is_identifier_name(column_name) or unique_percent >= 99.5:
            id_candidates.append(column_name)
    return id_candidates


def _compute_readiness(issues_output: dict) -> tuple[int, str]:
    penalties = {
        "none": 0,
        "none_detected": 0,
        "low": 8,
        "moderate": 18,
        "high": 32,
        "critical": 50,
    }
    score = 100
    score -= penalties.get(str(issues_output.get("missing_data", "none")), 0)
    score -= penalties.get(str(issues_output.get("duplicates", "none")), 0)
    score -= penalties.get(str(issues_output.get("outliers", "none")), 0)
    score -= penalties.get(str(issues_output.get("type_inconsistencies", "none_detected")), 0)
    score = max(0, min(100, score))

    if score >= 85:
        label = "ready"
    elif score >= 60:
        label = "needs_attention"
    else:
        label = "risky"
    return score, label


def _infer_role_sets(
    profile_output: dict,
    target_column: str | None,
    id_columns: list[str],
    cardinality: dict[str, dict],
    missing: dict[str, dict],
) -> dict[str, list[str]]:
    column_types = profile_output.get("column_types", {})
    columns = [str(column) for column in profile_output.get("column_names", [])]
    id_set = set(id_columns)

    numerical = [str(column) for column in column_types.get("numerical", [])]
    categorical = [str(column) for column in column_types.get("categorical", [])]
    boolean = [str(column) for column in column_types.get("boolean", [])]

    high_cardinality_categoricals = [
        column
        for column in categorical
        if float(cardinality.get(column, {}).get("unique_percent", 0.0)) >= 50.0
        or int(cardinality.get(column, {}).get("unique_count", 0)) >= 100
    ]

    excluded_by_default = set(id_set)
    for column in columns:
        missing_percent = float(missing.get(column, {}).get("missing_percent", 0.0))
        if missing_percent >= 70.0:
            excluded_by_default.add(column)
    excluded_by_default.update(high_cardinality_categoricals)
    if target_column:
        excluded_by_default.discard(target_column)

    target_set = {target_column} if target_column else set()
    numeric_features = [column for column in numerical if column not in excluded_by_default and column not in target_set]
    categorical_features = [
        column
        for column in categorical
        if column not in excluded_by_default and column not in target_set and column not in id_set
    ]
    boolean_features = [column for column in boolean if column not in excluded_by_default and column not in target_set]

    return {
        "id_columns": _ordered_subset(id_set, columns),
        "target_columns": _ordered_subset(target_set, columns),
        "numeric_features": _ordered_subset(numeric_features, columns),
        "categorical_features": _ordered_subset(categorical_features, columns),
        "boolean_features": _ordered_subset(boolean_features, columns),
        "high_cardinality_categoricals": _ordered_subset(high_cardinality_categoricals, columns),
        "excluded_by_default": _ordered_subset(excluded_by_default, columns),
    }


def _recommended_preprocessing(
    profile_output: dict,
    issues_output: dict,
    role_sets: dict[str, list[str]],
    missing: dict[str, dict],
) -> list[dict]:
    columns = [str(column) for column in profile_output.get("column_names", [])]
    id_columns = set(role_sets.get("id_columns", []))
    target_columns = set(role_sets.get("target_columns", []))
    excluded = set(role_sets.get("excluded_by_default", []))
    numerical = set(profile_output.get("column_types", {}).get("numerical", []))
    high_card = set(role_sets.get("high_cardinality_categoricals", []))

    actions: list[dict] = []
    for column in columns:
        if column in target_columns:
            actions.append(
                {
                    "column": column,
                    "operation": "set_as_target",
                    "strategy": "supervised_label",
                    "rationale": "Designated as the inferred target column.",
                }
            )
            continue

        if column in id_columns:
            actions.append(
                {
                    "column": column,
                    "operation": "exclude_column",
                    "strategy": "identifier",
                    "rationale": "Identifier-like column should be excluded from baseline feature set.",
                }
            )
            continue

        missing_percent = float(missing.get(column, {}).get("missing_percent", 0.0))
        if missing_percent > 0:
            if column in numerical:
                actions.append(
                    {
                        "column": column,
                        "operation": "impute_missing",
                        "strategy": "median",
                        "add_missing_indicator": missing_percent >= 5.0,
                        "rationale": "Numeric column contains missing values.",
                    }
                )
            elif missing_percent >= 70.0:
                actions.append(
                    {
                        "column": column,
                        "operation": "derive_indicator",
                        "new_column": f"has_{column.lower()}",
                        "strategy": "missingness_indicator",
                        "rationale": "High missingness column is better represented by a presence indicator.",
                    }
                )
                actions.append(
                    {
                        "column": column,
                        "operation": "exclude_column",
                        "strategy": "high_missingness_raw_feature",
                        "rationale": "Raw feature has very high missingness and is excluded by default.",
                    }
                )
            else:
                actions.append(
                    {
                        "column": column,
                        "operation": "impute_missing",
                        "strategy": "most_frequent",
                        "add_missing_indicator": missing_percent >= 5.0,
                        "rationale": "Categorical column contains missing values.",
                    }
                )

        if column in high_card and column not in excluded:
            actions.append(
                {
                    "column": column,
                    "operation": "encode_categorical",
                    "strategy": "frequency_or_target_encoding_with_cv",
                    "rationale": "High-cardinality categorical column requires non-one-hot encoding.",
                }
            )

    if str(issues_output.get("outliers", "none")) in {"moderate", "high"}:
        for column in role_sets.get("numeric_features", []):
            actions.append(
                {
                    "column": column,
                    "operation": "outlier_treatment",
                    "strategy": "winsorize_or_robust_scale",
                    "rationale": "Outlier severity indicates robust numeric preprocessing is recommended.",
                }
            )

    return actions


def build_modeling_contract(
    *,
    job_id: str,
    created_at: datetime,
    ingestion_output: dict,
    profile_output: dict,
    issues_output: dict,
    artifact_links: list[dict],
) -> dict:
    cardinality = _cardinality_map(profile_output)
    missing = _missing_map(profile_output)

    target_column, target_confidence, target_rationale = _infer_target_from_files(
        ingestion_output=ingestion_output,
        profile_output=profile_output,
        cardinality=cardinality,
    )
    problem_type, metric_hint = _infer_problem_type(
        target_column=target_column,
        profile_output=profile_output,
        cardinality=cardinality,
    )
    id_columns = _infer_id_columns(
        profile_output=profile_output,
        cardinality=cardinality,
        target_column=target_column,
    )
    readiness_score, readiness_label = _compute_readiness(issues_output)
    role_sets = _infer_role_sets(
        profile_output=profile_output,
        target_column=target_column,
        id_columns=id_columns,
        cardinality=cardinality,
        missing=missing,
    )

    source_metadata = ingestion_output.get("source_metadata", {})
    contract = {
        "schema_version": MODEL_CONTRACT_SCHEMA_VERSION,
        "job": {
            "job_id": job_id,
            "created_at": _to_iso(created_at),
            "source": ingestion_output.get("source"),
            "competition": ingestion_output.get("competition"),
            "selected_file": ingestion_output.get("selected_file"),
        },
        "source_metadata": {
            "files_detected": source_metadata.get("files_detected", []),
            "selected_train_file": source_metadata.get("selected_train_file"),
            "selected_test_file": source_metadata.get("selected_test_file"),
            "sample_submission_file": source_metadata.get("sample_submission_file"),
        },
        "task": {
            "inferred_problem_type": problem_type,
            "target_column": target_column,
            "target_confidence": target_confidence,
            "metric_hint": metric_hint,
            "rationale": target_rationale,
        },
        "dataset": {
            "rows": profile_output.get("rows"),
            "columns": profile_output.get("columns"),
            "readiness_label": readiness_label,
            "readiness_score": readiness_score,
        },
        "column_roles": role_sets,
        "quality_gates": {
            "missing_data": issues_output.get("missing_data"),
            "duplicates": issues_output.get("duplicates"),
            "outliers": issues_output.get("outliers"),
            "type_inconsistencies": issues_output.get("type_inconsistencies"),
        },
        "recommended_preprocessing": _recommended_preprocessing(
            profile_output=profile_output,
            issues_output=issues_output,
            role_sets=role_sets,
            missing=missing,
        ),
        "artifacts": artifact_links,
    }
    return contract
