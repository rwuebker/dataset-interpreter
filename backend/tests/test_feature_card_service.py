from app.services.feature_card_service import build_feature_cards


def test_feature_cards_use_column_specific_quality_signals() -> None:
    profile_output = {
        "rows": 891,
        "column_names": [
            "PassengerId",
            "Survived",
            "Pclass",
            "Name",
            "Sex",
            "Age",
            "Ticket",
            "Cabin",
        ],
        "column_types": {
            "numerical": ["PassengerId", "Survived", "Pclass", "Age"],
            "categorical": ["Name", "Sex", "Ticket", "Cabin"],
            "boolean": [],
        },
        "cardinality": [
            {"column": "PassengerId", "unique_count": 891, "unique_percent": 100.0},
            {"column": "Survived", "unique_count": 2, "unique_percent": 0.2245},
            {"column": "Pclass", "unique_count": 3, "unique_percent": 0.3367},
            {"column": "Name", "unique_count": 891, "unique_percent": 100.0},
            {"column": "Sex", "unique_count": 2, "unique_percent": 0.2245},
            {"column": "Age", "unique_count": 88, "unique_percent": 9.8765},
            {"column": "Ticket", "unique_count": 681, "unique_percent": 76.431},
            {"column": "Cabin", "unique_count": 147, "unique_percent": 16.4983},
        ],
        "missing_values": {
            "by_column": [
                {"column": "PassengerId", "missing_percent": 0.0},
                {"column": "Survived", "missing_percent": 0.0},
                {"column": "Pclass", "missing_percent": 0.0},
                {"column": "Name", "missing_percent": 0.0},
                {"column": "Sex", "missing_percent": 0.0},
                {"column": "Age", "missing_percent": 19.8653},
                {"column": "Ticket", "missing_percent": 0.0},
                {"column": "Cabin", "missing_percent": 77.1044},
            ]
        },
        "numeric_distributions": {"Age": {"p10": 14, "p50": 28, "p90": 50, "std": 14.5}},
        "numeric_histograms": {"Age": {"bins": [0.0, 20.0, 40.0, 80.0], "counts": [120, 300, 200]}},
        "top_values": {
            "Sex": [{"value": "male", "count": 577}, {"value": "female", "count": 314}],
            "Cabin": [{"value": "<NA>", "count": 687}],
        },
    }
    issues_output = {
        "missing_data": "moderate",
        "issues": [
            {
                "issue_type": "type_inconsistencies",
                "severity": "moderate",
                "affected_columns": ["Ticket"],
            }
        ],
        "summary": {
            "rows_analyzed": 891,
            "inconsistent_columns": ["Ticket"],
            "outlier_columns": {"Age": 35, "Pclass": 0},
        },
    }
    modeling_contract = {
        "column_roles": {
            "id_columns": ["PassengerId"],
            "target_columns": ["Survived"],
            "numeric_features": ["Pclass", "Age"],
            "categorical_features": ["Sex"],
            "boolean_features": [],
            "high_cardinality_categoricals": ["Name", "Ticket", "Cabin"],
            "excluded_by_default": ["PassengerId", "Name", "Ticket", "Cabin"],
        }
    }

    cards = build_feature_cards(profile_output, issues_output, modeling_contract)
    by_column = {card["column"]: card for card in cards}

    assert by_column["Sex"]["quality_status"] == "healthy"
    assert by_column["Pclass"]["quality_status"] == "healthy"
    assert by_column["Age"]["quality_status"] == "needs_attention"
    assert by_column["Ticket"]["quality_status"] in {"needs_attention", "risky"}
    assert by_column["Cabin"]["quality_status"] == "risky"
    assert by_column["Name"]["role"] == "excluded"
    assert by_column["Name"]["semantic_type"] == "text_like"
    assert by_column["Sex"]["chart"]["type"] == "bar"
    assert by_column["Age"]["chart"]["type"] == "histogram"
