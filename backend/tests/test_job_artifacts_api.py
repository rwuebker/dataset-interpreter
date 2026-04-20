import json
import time

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _create_completed_job() -> dict:
    create_response = client.post(
        "/jobs/create",
        json={"source_type": "kaggle", "kaggle": {"competition": "titanic"}},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    deadline = time.time() + 10
    while time.time() < deadline:
        poll = client.get(f"/jobs/{job_id}")
        assert poll.status_code == 200
        payload = poll.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.2)

    raise AssertionError("Timed out waiting for job completion")


def test_job_summary_and_manifest_endpoints() -> None:
    final_payload = _create_completed_job()
    assert final_payload["status"] == "completed"
    assert "/Users/" not in json.dumps(final_payload)
    job_id = final_payload["job_id"]

    summary_response = client.get(f"/jobs/{job_id}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["job_id"] == job_id
    assert summary["status"] == "completed"
    assert "artifacts" in summary
    assert "/Users/" not in json.dumps(summary)

    artifacts_response = client.get(f"/jobs/{job_id}/artifacts")
    assert artifacts_response.status_code == 200
    manifest = artifacts_response.json()
    assert manifest["job_id"] == job_id
    artifact_ids = {item["artifact_id"] for item in manifest["artifacts"]}
    assert {
        "manifest",
        "dataset_report",
        "data_profile",
        "issue_report",
        "interpretation",
        "feature_cards",
        "cleaning_plan",
        "cleaning_receipt",
        "modeling_contract",
    }.issubset(artifact_ids)
    assert "/Users/" not in json.dumps(manifest)


def test_artifact_download_endpoints_return_expected_content() -> None:
    final_payload = _create_completed_job()
    assert final_payload["status"] == "completed"
    job_id = final_payload["job_id"]

    manifest = client.get(f"/jobs/{job_id}/artifacts").json()
    artifact_ids = {item["artifact_id"] for item in manifest["artifacts"]}

    contract_response = client.get(f"/jobs/{job_id}/artifacts/modeling_contract")
    assert contract_response.status_code == 200
    assert contract_response.headers["content-type"].startswith("application/json")
    assert contract_response.json()["schema_version"] == "dataset_interpreter.modeling_contract.v1"

    cards_response = client.get(f"/jobs/{job_id}/artifacts/feature_cards")
    assert cards_response.status_code == 200
    cards_text = cards_response.text.strip()
    assert cards_text
    card_lines = [line for line in cards_text.splitlines() if line.strip()]
    profile_columns = len(final_payload["result"]["dataset_profile"]["column_names"])
    assert len(card_lines) == profile_columns

    plan_response = client.get(f"/jobs/{job_id}/artifacts/cleaning_plan")
    receipt_response = client.get(f"/jobs/{job_id}/artifacts/cleaning_receipt")
    assert plan_response.status_code == 200
    assert receipt_response.status_code == 200
    assert plan_response.json()["schema_version"] == "dataset_interpreter.cleaning_plan.v1"
    assert receipt_response.json()["schema_version"] == "dataset_interpreter.cleaning_receipt.v1"

    if "cleaned_train_csv" in artifact_ids:
        cleaned_response = client.get(f"/jobs/{job_id}/artifacts/cleaned_train_csv")
        assert cleaned_response.status_code == 200
        assert "text/csv" in cleaned_response.headers.get("content-type", "")
