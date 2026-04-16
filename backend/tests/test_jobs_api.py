import time

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_job_kaggle_and_complete_pipeline() -> None:
    create_response = client.post(
        "/jobs/create",
        json={"source_type": "kaggle", "kaggle": {"competition": "titanic"}},
    )

    assert create_response.status_code == 200
    create_payload = create_response.json()
    assert create_payload["status"] == "pending"
    assert create_payload["job_id"]

    job_id = create_payload["job_id"]
    deadline = time.time() + 8
    final_payload = None

    while time.time() < deadline:
        poll_response = client.get(f"/jobs/{job_id}")
        assert poll_response.status_code == 200
        payload = poll_response.json()

        assert payload["job_id"] == job_id
        assert payload["status"] in {"pending", "running", "completed", "failed"}
        assert "created_at" in payload
        assert "updated_at" in payload

        if payload["status"] in {"completed", "failed"}:
            final_payload = payload
            break

        time.sleep(0.2)

    assert final_payload is not None
    assert final_payload["status"] == "completed"
    assert final_payload["current_stage"] == "interpretation"
    assert final_payload["progress"] == 100
    assert final_payload["error"] is None
    assert "dataset_profile" in final_payload["result"]
    assert "detected_issues" in final_payload["result"]
    assert "ai_interpretation" in final_payload["result"]
    assert "cleaned_dataset" in final_payload["result"]


def test_create_job_csv_upload_is_not_implemented_yet() -> None:
    response = client.post(
        "/jobs/create",
        json={"source_type": "csv_upload", "csv_upload": {"filename": "example.csv"}},
    )

    assert response.status_code == 501
    assert "not implemented yet" in response.json()["detail"].lower()
