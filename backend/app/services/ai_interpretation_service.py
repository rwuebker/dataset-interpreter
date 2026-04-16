import asyncio
from typing import Any

from app.clients.llm_client import LLMClient
from app.core.config import settings


def _fallback_interpretation(profile_output: dict, issues_output: dict, note: str) -> dict:
    key_risks = [
        f"Missing data severity is '{issues_output.get('missing_data', 'unknown')}'.",
        f"Duplicate severity is '{issues_output.get('duplicates', 'unknown')}'.",
        "Target definition and metric selection may be unclear.",
    ]
    suggested_next_steps = [
        "Review highest-severity issues first.",
        "Finalize train/validation split and leakage checks.",
        "Train a baseline model using cleaned feature set.",
    ]

    return {
        "dataset_representation": "Likely a supervised tabular prediction dataset.",
        "likely_ml_problem": "classification",
        "key_risks": key_risks,
        "suggested_next_steps": suggested_next_steps,
        # Backward-compatible aliases for existing consumers.
        "key_concerns": key_risks,
        "recommended_next_steps": suggested_next_steps,
        "grounding": {
            "rows": profile_output.get("rows"),
            "columns": profile_output.get("columns"),
            "missing_data": issues_output.get("missing_data"),
            "top_issue_count": len(issues_output.get("prioritized_issues", [])),
        },
        "note": note,
    }


def _normalize_llm_output(parsed: dict[str, Any], profile_output: dict, issues_output: dict) -> dict:
    def _coerce_list(value: Any, default_message: str) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            parts = [segment.strip("-• \t") for segment in value.replace(";", "\n").splitlines()]
            cleaned = [part for part in parts if part]
            if cleaned:
                return cleaned
        return [default_message]

    key_risks = _coerce_list(
        parsed.get("key_risks") if parsed.get("key_risks") is not None else parsed.get("key_concerns"),
        "LLM response did not include structured key concerns.",
    )
    suggested_next_steps = _coerce_list(
        parsed.get("suggested_next_steps")
        if parsed.get("suggested_next_steps") is not None
        else parsed.get("recommended_next_steps"),
        "Define immediate cleanup and baseline-model plan.",
    )

    return {
        "dataset_representation": str(parsed.get("dataset_representation", "Dataset representation not provided.")),
        "likely_ml_problem": str(parsed.get("likely_ml_problem", "unknown")),
        "key_risks": [str(item) for item in key_risks][:6],
        "suggested_next_steps": [str(item) for item in suggested_next_steps][:6],
        # Backward-compatible aliases for existing consumers.
        "key_concerns": [str(item) for item in key_risks][:6],
        "recommended_next_steps": [str(item) for item in suggested_next_steps][:6],
        "grounding": {
            "rows": profile_output.get("rows"),
            "columns": profile_output.get("columns"),
            "missing_data": issues_output.get("missing_data"),
            "prioritized_issues": issues_output.get("prioritized_issues", [])[:3],
        },
        "note": "OpenAI interpretation generated from computed profile and issue outputs.",
    }


def _build_prompt_payload(profile_output: dict, issues_output: dict) -> dict:
    return {
        "dataset_profile": {
            "rows": profile_output.get("rows"),
            "columns": profile_output.get("columns"),
            "column_types": profile_output.get("column_types"),
            "missing_values": profile_output.get("missing_values"),
            "numeric_summary": profile_output.get("numeric_summary"),
        },
        "detected_issues": {
            "missing_data": issues_output.get("missing_data"),
            "duplicates": issues_output.get("duplicates"),
            "outliers": issues_output.get("outliers"),
            "type_inconsistencies": issues_output.get("type_inconsistencies"),
            "prioritized_issues": issues_output.get("prioritized_issues"),
        },
    }


def _run_openai_interpretation(profile_output: dict, issues_output: dict) -> dict:
    if not settings.openai_api_key:
        return _fallback_interpretation(
            profile_output,
            issues_output,
            note="Fallback interpretation used (OPENAI_API_KEY not configured).",
        )

    prompt_payload = _build_prompt_payload(profile_output, issues_output)
    llm_client = LLMClient(api_key=settings.openai_api_key, model=settings.openai_model)
    parsed = llm_client.generate_dataset_interpretation(prompt_payload)
    return _normalize_llm_output(parsed, profile_output, issues_output)


async def run_ai_interpretation(profile_output: dict, issues_output: dict) -> dict:
    if not settings.enable_real_ai_interpretation:
        return _fallback_interpretation(
            profile_output,
            issues_output,
            note="Fallback interpretation used (real AI interpretation disabled).",
        )

    try:
        return await asyncio.to_thread(_run_openai_interpretation, profile_output, issues_output)
    except Exception as exc:
        return _fallback_interpretation(
            profile_output,
            issues_output,
            note=f"Fallback interpretation used after OpenAI error: {exc}",
        )
