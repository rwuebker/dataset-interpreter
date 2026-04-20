from __future__ import annotations


FEATURE_CARDS_SCHEMA_VERSION = "dataset_interpreter.feature_cards.v1"


def _cardinality_map(profile_output: dict) -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for item in profile_output.get("cardinality", []):
        column = str(item.get("column", ""))
        if column:
            mapping[column] = item
    return mapping


def _missing_map(profile_output: dict) -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for item in profile_output.get("missing_values", {}).get("by_column", []):
        column = str(item.get("column", ""))
        if column:
            mapping[column] = item
    return mapping


def _role_lookup(modeling_contract: dict) -> dict[str, str]:
    roles = modeling_contract.get("column_roles", {})
    role_by_column: dict[str, str] = {}
    for column in roles.get("id_columns", []):
        role_by_column[str(column)] = "id"
    for column in roles.get("target_columns", []):
        role_by_column[str(column)] = "target"
    for column in roles.get("excluded_by_default", []):
        role_by_column.setdefault(str(column), "excluded")
    for column in roles.get("numeric_features", []):
        role_by_column.setdefault(str(column), "feature")
    for column in roles.get("categorical_features", []):
        role_by_column.setdefault(str(column), "feature")
    for column in roles.get("boolean_features", []):
        role_by_column.setdefault(str(column), "feature")
    return role_by_column


def _is_text_like_column_name(column: str) -> bool:
    normalized = column.strip().lower()
    return normalized in {"name", "full_name", "description", "text", "title"}


def _physical_type(column: str, profile_output: dict) -> str:
    column_types = profile_output.get("column_types", {})
    if column in set(column_types.get("boolean", [])):
        return "boolean"
    if column in set(column_types.get("numerical", [])):
        numeric_summary = profile_output.get("numeric_summary", {}).get(column, {})
        min_value = numeric_summary.get("min")
        max_value = numeric_summary.get("max")
        if min_value is not None and max_value is not None and float(min_value).is_integer() and float(max_value).is_integer():
            return "integer"
        return "float"
    if column in set(column_types.get("categorical", [])):
        return "string"
    return "unknown"


def _semantic_type(
    *,
    column: str,
    role: str,
    physical_type: str,
    unique_percent: float,
    unique_count: int,
) -> str:
    if role == "id":
        return "identifier"
    if role == "target":
        if unique_count == 2:
            return "binary_label"
        return "numeric_discrete" if physical_type in {"integer", "float"} else "unknown"

    if physical_type in {"integer", "float"}:
        if unique_count <= 20:
            return "numeric_discrete"
        return "numeric_continuous"

    if physical_type == "string":
        if _is_text_like_column_name(column) or (unique_percent >= 85.0 and unique_count >= 100):
            return "text_like"
        if unique_percent >= 50 or unique_count >= 100:
            return "categorical_high_cardinality"
        return "categorical_low_cardinality"

    if physical_type == "boolean":
        return "binary_label"

    return "unknown"


def _quality_status(
    *,
    role: str,
    missing_percent: float,
    has_type_inconsistency: bool,
    outlier_ratio: float,
    semantic_type: str,
) -> str:
    if role == "target":
        if missing_percent > 0:
            return "risky"
        return "healthy"
    if role == "id":
        return "healthy"
    if role == "excluded":
        if missing_percent >= 70:
            return "risky"
        if has_type_inconsistency:
            return "needs_attention"
        return "healthy"

    score = 0
    if has_type_inconsistency:
        score += 3

    if missing_percent >= 40:
        score += 3
    elif missing_percent >= 10:
        score += 2
    elif missing_percent > 0.5:
        score += 1

    if outlier_ratio >= 0.08:
        score += 2
    elif outlier_ratio >= 0.02:
        score += 1

    if semantic_type in {"categorical_high_cardinality", "text_like"}:
        score += 1

    if score >= 4:
        return "risky"
    if score >= 1:
        return "needs_attention"
    return "healthy"


def _action_and_use(
    *,
    role: str,
    semantic_type: str,
    missing_percent: float,
    quality_status: str,
    has_type_inconsistency: bool,
    outlier_ratio: float,
) -> tuple[str, str, str]:
    if role == "target":
        return "Set as supervised target.", "target", "Column selected as target candidate."
    if role == "id":
        return "Exclude from baseline model features.", "id", "Identifier-like column."
    if role == "excluded":
        if semantic_type == "text_like":
            return (
                "Exclude from baseline model; optional feature engineering can derive title-like tokens.",
                "no",
                "Text-like column is excluded by default to avoid noisy sparse features.",
            )
        if missing_percent >= 70:
            return "Derive missingness indicator and exclude raw column.", "no", "Very high missingness."
        return "Exclude by default; include only with explicit justification.", "no", "Excluded by default by contract."

    if has_type_inconsistency:
        return (
            "Normalize mixed data types before feature engineering.",
            "maybe",
            "Column has mixed numeric/non-numeric patterns.",
        )
    if outlier_ratio >= 0.02 and semantic_type in {"numeric_continuous", "numeric_discrete"}:
        return (
            "Use robust scaling or winsorization before baseline modeling.",
            "yes",
            "Column contains notable outlier density.",
        )
    if semantic_type == "categorical_high_cardinality":
        return "Use frequency/target encoding with leakage-safe CV.", "maybe", "High-cardinality categorical feature."
    if semantic_type == "text_like":
        return "Exclude by default or derive compact text indicators.", "maybe", "Text-like free-form feature."
    if quality_status == "risky":
        return "Review and remediate quality issues before modeling.", "maybe", "Feature has high-risk data quality signals."
    if missing_percent > 0:
        return "Impute missing values and add indicator if needed.", "yes", "Feature is usable after missing-value treatment."
    return "Use in baseline feature set.", "yes", "Feature appears healthy for baseline modeling."


def _issue_signals(issues_output: dict) -> tuple[set[str], dict[str, int], int]:
    inconsistent_columns = set(str(column) for column in issues_output.get("summary", {}).get("inconsistent_columns", []))
    outlier_columns_raw = issues_output.get("summary", {}).get("outlier_columns", {}) or {}
    outlier_columns: dict[str, int] = {str(column): int(count) for column, count in outlier_columns_raw.items()}
    rows_analyzed = int(issues_output.get("summary", {}).get("rows_analyzed", 0))

    for issue in issues_output.get("issues", []):
        if issue.get("issue_type") == "type_inconsistencies":
            for column in issue.get("affected_columns", []):
                inconsistent_columns.add(str(column))

    return inconsistent_columns, outlier_columns, rows_analyzed


def _build_chart_payload(column: str, physical: str, profile_output: dict) -> dict | None:
    histograms = profile_output.get("numeric_histograms", {})
    top_values = profile_output.get("top_values", {})

    if physical in {"integer", "float"}:
        histogram = histograms.get(column, {})
        bins = histogram.get("bins", [])
        counts = histogram.get("counts", [])
        if isinstance(bins, list) and isinstance(counts, list) and len(bins) >= 2 and len(counts) >= 1:
            return {
                "type": "histogram",
                "bins": bins,
                "counts": counts,
            }

    column_top_values = top_values.get(column, [])
    if isinstance(column_top_values, list) and column_top_values:
        return {
            "type": "bar",
            "values": [
                {
                    "label": str(item.get("value", "")),
                    "count": int(item.get("count", 0)),
                }
                for item in column_top_values
            ],
        }
    return None


def build_feature_cards(profile_output: dict, issues_output: dict, modeling_contract: dict) -> list[dict]:
    columns = [str(column) for column in profile_output.get("column_names", [])]
    role_by_column = _role_lookup(modeling_contract)
    cardinality = _cardinality_map(profile_output)
    missing = _missing_map(profile_output)

    inconsistent_columns, outlier_columns, rows_analyzed = _issue_signals(issues_output)
    rows_for_ratio = max(rows_analyzed or int(profile_output.get("rows", 0)) or 1, 1)

    distributions = profile_output.get("numeric_distributions", {})
    top_values = profile_output.get("top_values", {})

    cards: list[dict] = []
    for column in columns:
        role = role_by_column.get(column, "unknown")
        card_stats = cardinality.get(column, {})
        unique_count = int(card_stats.get("unique_count", 0))
        unique_percent = float(card_stats.get("unique_percent", 0.0))
        missing_percent = float(missing.get(column, {}).get("missing_percent", 0.0))
        physical = _physical_type(column, profile_output)
        semantic = _semantic_type(
            column=column,
            role=role,
            physical_type=physical,
            unique_percent=unique_percent,
            unique_count=unique_count,
        )
        has_type_inconsistency = column in inconsistent_columns
        outlier_ratio = float(outlier_columns.get(column, 0)) / float(rows_for_ratio)
        quality = _quality_status(
            role=role,
            missing_percent=missing_percent,
            has_type_inconsistency=has_type_inconsistency,
            outlier_ratio=outlier_ratio,
            semantic_type=semantic,
        )
        action, use_in_model, rationale = _action_and_use(
            role=role,
            semantic_type=semantic,
            missing_percent=missing_percent,
            quality_status=quality,
            has_type_inconsistency=has_type_inconsistency,
            outlier_ratio=outlier_ratio,
        )

        card = {
            "schema_version": FEATURE_CARDS_SCHEMA_VERSION,
            "column": column,
            "role": role,
            "physical_type": physical,
            "semantic_type": semantic,
            "missing_percent": missing_percent,
            "unique_count": unique_count,
            "unique_percent": unique_percent,
            "quality_status": quality,
            "recommended_action": action,
            "use_in_model": use_in_model,
            "rationale": rationale,
            "outlier_ratio": outlier_ratio,
            "type_inconsistency": has_type_inconsistency,
        }
        if column in distributions:
            card["distribution"] = distributions[column]
        if column in top_values:
            card["top_values"] = top_values[column]
        chart_payload = _build_chart_payload(column, physical, profile_output)
        if chart_payload is not None:
            card["chart"] = chart_payload
        cards.append(card)

    return cards
