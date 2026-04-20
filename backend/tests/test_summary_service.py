from app.services.summary_service import build_job_summary


def test_summary_prefers_deterministic_modeling_contract_steps() -> None:
    job_payload = {
        "job_id": "job123",
        "status": "completed",
        "result": {
            "dataset_profile": {"rows": 100, "columns": 5},
            "detected_issues": {"issues": []},
            "ai_interpretation": {
                "suggested_next_steps": [
                    "Impute Cabin using most frequent value.",
                    "Apply generic scaling.",
                ]
            },
            "pipeline_summary": {"source": "kaggle", "competition": "titanic", "selected_file": "train.csv"},
            "modeling_contract": {
                "task": {"inferred_problem_type": "binary_classification", "target_column": "Survived"},
                "dataset": {"readiness_label": "needs_attention", "readiness_score": 64},
                "recommended_preprocessing": [
                    {
                        "column": "Cabin",
                        "operation": "derive_indicator",
                        "new_column": "has_cabin",
                        "strategy": "missingness_indicator",
                    },
                    {
                        "column": "Cabin",
                        "operation": "exclude_column",
                        "strategy": "high_missingness_raw_feature",
                    },
                ],
            },
        },
    }

    summary = build_job_summary(job_payload, manifest_payload=None)
    recommended = [item.lower() for item in summary["recommended_next_steps"]]

    assert any("derive" in item and "cabin" in item for item in recommended)
    assert any("exclude" in item and "cabin" in item for item in recommended)
    assert not any("impute cabin" in item for item in recommended)
