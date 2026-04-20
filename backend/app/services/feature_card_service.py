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
    issue_severity: str,
    semantic_type: str,
) -> str:
    if role == "target":
        if missing_percent > 0:
            return "risky"
        return "healthy"

    if missing_percent >= 50:
        return "risky"
    if issue_severity in {"high", "critical"}:
        return "risky"
    if missing_percent >= 10 or issue_severity == "moderate":
        return "needs_attention"
    if semantic_type == "categorical_high_cardinality":
        return "needs_attention"
    return "healthy"


def _action_and_use(role: str, semantic_type: str, missing_percent: float, quality_status: str) -> tuple[str, str, str]:
    if role == "target":
        return "Set as supervised target.", "target", "Column selected as target candidate."
    if role == "id":
        return "Exclude from baseline model features.", "id", "Identifier-like column."
    if role == "excluded":
        if missing_percent >= 70:
            return "Derive missingness indicator and exclude raw column.", "no", "Very high missingness."
        return "Exclude by default; include only with explicit justification.", "no", "Excluded by default by contract."

    if semantic_type == "categorical_high_cardinality":
        return "Use frequency/target encoding with leakage-safe CV.", "maybe", "High-cardinality categorical feature."
    if quality_status == "risky":
        return "Review and remediate quality issues before modeling.", "maybe", "Feature has high-risk data quality signals."
    if missing_percent > 0:
        return "Impute missing values and add indicator if needed.", "yes", "Feature is usable after missing-value treatment."
    return "Use in baseline feature set.", "yes", "Feature appears healthy for baseline modeling."


def build_feature_cards(profile_output: dict, issues_output: dict, modeling_contract: dict) -> list[dict]:
    columns = [str(column) for column in profile_output.get("column_names", [])]
    role_by_column = _role_lookup(modeling_contract)
    cardinality = _cardinality_map(profile_output)
    missing = _missing_map(profile_output)

    issue_lookup: dict[str, str] = {}
    for issue in issues_output.get("issues", []):
        severity = str(issue.get("severity", "low"))
        for affected in issue.get("affected_columns", []):
            issue_lookup[str(affected)] = severity

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
            role=role,
            physical_type=physical,
            unique_percent=unique_percent,
            unique_count=unique_count,
        )
        issue_severity = issue_lookup.get(column, str(issues_output.get("missing_data", "low")))
        quality = _quality_status(
            role=role,
            missing_percent=missing_percent,
            issue_severity=issue_severity,
            semantic_type=semantic,
        )
        action, use_in_model, rationale = _action_and_use(
            role=role,
            semantic_type=semantic,
            missing_percent=missing_percent,
            quality_status=quality,
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
        }
        if column in distributions:
            card["distribution"] = distributions[column]
        if column in top_values:
            card["top_values"] = top_values[column]
        cards.append(card)

    return cards
