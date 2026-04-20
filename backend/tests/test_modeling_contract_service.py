from datetime import datetime, timezone

from app.services.modeling_contract_service import build_modeling_contract


def test_modeling_contract_infers_titanic_like_roles() -> None:
    ingestion_output = {
        "source": "kaggle",
        "competition": "titanic",
        "selected_file": "train.csv",
        "source_metadata": {
            "files_detected": ["train.csv", "test.csv", "sample_submission.csv"],
            "selected_train_file": "train.csv",
            "selected_test_file": "test.csv",
            "sample_submission_file": "sample_submission.csv",
            "file_columns": {
                "train.csv": [
                    "PassengerId",
                    "Survived",
                    "Pclass",
                    "Name",
                    "Sex",
                    "Age",
                    "SibSp",
                    "Parch",
                    "Ticket",
                    "Fare",
                    "Cabin",
                    "Embarked",
                ],
                "test.csv": [
                    "PassengerId",
                    "Pclass",
                    "Name",
                    "Sex",
                    "Age",
                    "SibSp",
                    "Parch",
                    "Ticket",
                    "Fare",
                    "Cabin",
                    "Embarked",
                ],
                "sample_submission.csv": ["PassengerId", "Survived"],
            },
        },
    }
    profile_output = {
        "rows": 891,
        "columns": 12,
        "column_names": [
            "PassengerId",
            "Survived",
            "Pclass",
            "Name",
            "Sex",
            "Age",
            "SibSp",
            "Parch",
            "Ticket",
            "Fare",
            "Cabin",
            "Embarked",
        ],
        "column_types": {
            "numerical": ["PassengerId", "Survived", "Pclass", "Age", "SibSp", "Parch", "Fare"],
            "categorical": ["Name", "Sex", "Ticket", "Cabin", "Embarked"],
            "boolean": [],
        },
        "cardinality": [
            {"column": "PassengerId", "unique_count": 891, "unique_percent": 100.0},
            {"column": "Survived", "unique_count": 2, "unique_percent": 0.2245},
            {"column": "Pclass", "unique_count": 3, "unique_percent": 0.3367},
            {"column": "Name", "unique_count": 891, "unique_percent": 100.0},
            {"column": "Sex", "unique_count": 2, "unique_percent": 0.2245},
            {"column": "Age", "unique_count": 88, "unique_percent": 9.8765},
            {"column": "SibSp", "unique_count": 7, "unique_percent": 0.7856},
            {"column": "Parch", "unique_count": 7, "unique_percent": 0.7856},
            {"column": "Ticket", "unique_count": 681, "unique_percent": 76.431},
            {"column": "Fare", "unique_count": 248, "unique_percent": 27.8339},
            {"column": "Cabin", "unique_count": 147, "unique_percent": 16.4983},
            {"column": "Embarked", "unique_count": 3, "unique_percent": 0.3367},
        ],
        "missing_values": {
            "by_column": [
                {"column": "Age", "missing_percent": 19.8653},
                {"column": "Cabin", "missing_percent": 77.1044},
                {"column": "Embarked", "missing_percent": 0.2245},
            ]
        },
    }
    issues_output = {
        "missing_data": "moderate",
        "duplicates": "none",
        "outliers": "moderate",
        "type_inconsistencies": "detected",
    }
    artifact_links = [
        {"artifact_id": "modeling_contract", "download_url": "/jobs/job123/artifacts/modeling_contract"}
    ]

    contract = build_modeling_contract(
        job_id="job123",
        created_at=datetime.now(timezone.utc),
        ingestion_output=ingestion_output,
        profile_output=profile_output,
        issues_output=issues_output,
        artifact_links=artifact_links,
    )

    assert contract["schema_version"] == "dataset_interpreter.modeling_contract.v1"
    assert contract["task"]["inferred_problem_type"] == "binary_classification"
    assert contract["task"]["target_column"] == "Survived"
    assert "PassengerId" in contract["column_roles"]["id_columns"]
    assert "PassengerId" in contract["column_roles"]["excluded_by_default"]
    assert "Pclass" in contract["column_roles"]["numeric_features"]
    assert "Sex" in contract["column_roles"]["categorical_features"]
    assert "Ticket" in contract["column_roles"]["high_cardinality_categoricals"]
