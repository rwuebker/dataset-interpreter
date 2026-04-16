import asyncio
from types import SimpleNamespace

import app.services.ai_interpretation_service as interpretation_service


def _sample_profile() -> dict:
    return {
        "rows": 100,
        "columns": 5,
        "column_types": {"numerical": ["x1"], "categorical": ["c1"], "boolean": []},
        "missing_values": {"missing_percent": 2.5},
        "numeric_summary": {"x1": {"mean": 1.0}},
    }


def _sample_issues() -> dict:
    return {
        "missing_data": "moderate",
        "duplicates": "low",
        "outliers": "none",
        "type_inconsistencies": "none_detected",
        "prioritized_issues": [{"issue_type": "missing_data", "severity_score": 2}],
    }


def test_ai_interpretation_uses_fallback_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        interpretation_service,
        "settings",
        SimpleNamespace(enable_real_ai_interpretation=False, openai_api_key=None, openai_model="gpt-4.1-mini"),
    )

    result = asyncio.run(interpretation_service.run_ai_interpretation(_sample_profile(), _sample_issues()))

    assert result["likely_ml_problem"] == "classification"
    assert "Fallback interpretation used" in result["note"]


def test_ai_interpretation_uses_llm_client_when_enabled(monkeypatch) -> None:
    class FakeLLMClient:
        def __init__(self, api_key: str, model: str) -> None:
            assert api_key == "test-key"
            assert model == "gpt-4.1-mini"

        def generate_dataset_interpretation(self, prompt_payload: dict) -> dict:
            assert "dataset_profile" in prompt_payload
            assert "detected_issues" in prompt_payload
            return {
                "dataset_representation": "Customer churn dataset",
                "likely_ml_problem": "classification",
                "key_concerns": ["Missing values in tenure"],
                "recommended_next_steps": ["Impute tenure then baseline model"],
            }

    monkeypatch.setattr(interpretation_service, "LLMClient", FakeLLMClient)
    monkeypatch.setattr(
        interpretation_service,
        "settings",
        SimpleNamespace(enable_real_ai_interpretation=True, openai_api_key="test-key", openai_model="gpt-4.1-mini"),
    )

    result = asyncio.run(interpretation_service.run_ai_interpretation(_sample_profile(), _sample_issues()))

    assert result["dataset_representation"] == "Customer churn dataset"
    assert result["likely_ml_problem"] == "classification"
    assert result["note"].startswith("OpenAI interpretation")


def test_ai_interpretation_coerces_string_lists_from_llm(monkeypatch) -> None:
    class FakeLLMClient:
        def __init__(self, api_key: str, model: str) -> None:
            pass

        def generate_dataset_interpretation(self, prompt_payload: dict) -> dict:
            return {
                "dataset_representation": "Marketing campaign table",
                "likely_ml_problem": "classification",
                "key_concerns": "Missing values in age; class imbalance",
                "recommended_next_steps": "- Impute age\n- Balance classes",
            }

    monkeypatch.setattr(interpretation_service, "LLMClient", FakeLLMClient)
    monkeypatch.setattr(
        interpretation_service,
        "settings",
        SimpleNamespace(enable_real_ai_interpretation=True, openai_api_key="test-key", openai_model="gpt-4.1-mini"),
    )

    result = asyncio.run(interpretation_service.run_ai_interpretation(_sample_profile(), _sample_issues()))

    assert result["key_concerns"] == ["Missing values in age", "class imbalance"]
    assert result["recommended_next_steps"] == ["Impute age", "Balance classes"]


def test_ai_interpretation_falls_back_after_llm_error(monkeypatch) -> None:
    class FailingLLMClient:
        def __init__(self, api_key: str, model: str) -> None:
            pass

        def generate_dataset_interpretation(self, prompt_payload: dict) -> dict:
            raise RuntimeError("simulated llm failure")

    monkeypatch.setattr(interpretation_service, "LLMClient", FailingLLMClient)
    monkeypatch.setattr(
        interpretation_service,
        "settings",
        SimpleNamespace(enable_real_ai_interpretation=True, openai_api_key="test-key", openai_model="gpt-4.1-mini"),
    )

    result = asyncio.run(interpretation_service.run_ai_interpretation(_sample_profile(), _sample_issues()))

    assert result["likely_ml_problem"] == "classification"
    assert "after OpenAI error" in result["note"]
