from __future__ import annotations


def build_job_summary(job_payload: dict, manifest_payload: dict | None) -> dict:
    result = job_payload.get("result") or {}
    profile = result.get("dataset_profile") or {}
    issues = result.get("detected_issues") or {}
    interpretation = result.get("ai_interpretation") or {}
    pipeline_summary = result.get("pipeline_summary") or {}
    modeling_contract = result.get("modeling_contract") or {}

    artifacts = []
    if manifest_payload:
        for item in manifest_payload.get("artifacts", []):
            artifacts.append(
                {
                    "artifact_id": item.get("artifact_id"),
                    "filename": item.get("filename"),
                    "content_type": item.get("content_type"),
                    "download_url": item.get("download_url"),
                }
            )

    top_issues = []
    for item in (issues.get("prioritized_issues") or issues.get("issues") or [])[:3]:
        top_issues.append(
            {
                "issue_type": item.get("issue_type", "unknown"),
                "severity": item.get("severity", "unknown"),
            }
        )

    recommended_next_steps = interpretation.get("suggested_next_steps")
    if not recommended_next_steps:
        recommended_next_steps = interpretation.get("recommended_next_steps", [])

    task = modeling_contract.get("task", {})
    dataset = modeling_contract.get("dataset", {})

    return {
        "job_id": job_payload.get("job_id"),
        "status": job_payload.get("status"),
        "source": pipeline_summary.get("source"),
        "competition": pipeline_summary.get("competition"),
        "selected_file": pipeline_summary.get("selected_file"),
        "rows": profile.get("rows"),
        "columns": profile.get("columns"),
        "inferred_problem_type": task.get("inferred_problem_type", "unknown"),
        "inferred_target_column": task.get("target_column"),
        "target_confidence": task.get("target_confidence"),
        "readiness_label": dataset.get("readiness_label"),
        "readiness_score": dataset.get("readiness_score"),
        "top_issues": top_issues,
        "recommended_next_steps": [str(step) for step in recommended_next_steps][:6],
        "artifacts": artifacts,
    }
