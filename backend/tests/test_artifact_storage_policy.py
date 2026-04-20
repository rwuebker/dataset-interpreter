import json
import time

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def _wait_for_completion(job_id: str) -> dict:
    deadline = time.time() + 12
    while time.time() < deadline:
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.2)
    raise AssertionError("Timed out waiting for job completion")


def _create_job(*, dataset_id: str | None = None) -> dict:
    request_payload = {"source_type": "kaggle", "kaggle": {"competition": "titanic"}}
    if dataset_id is not None:
        request_payload["dataset_id"] = dataset_id
    create_response = client.post("/jobs/create", json=request_payload)
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]
    final_payload = _wait_for_completion(job_id)
    assert final_payload["status"] == "completed"
    return final_payload


def test_artifact_storage_overwrite_and_dataset_persistence() -> None:
    competition_root = settings.dataset_storage_root / "titanic" / "_artifacts"
    current_manifest_path = competition_root / "current" / "manifest.json"
    dataset_manifest_path = competition_root / "by_dataset" / "demo_v1" / "manifest.json"

    first_current = _create_job()
    first_job_id = first_current["job_id"]
    assert current_manifest_path.exists()
    assert json.loads(current_manifest_path.read_text(encoding="utf-8"))["job_id"] == first_job_id

    persistent = _create_job(dataset_id="demo_v1")
    persistent_job_id = persistent["job_id"]
    assert dataset_manifest_path.exists()
    assert json.loads(dataset_manifest_path.read_text(encoding="utf-8"))["job_id"] == persistent_job_id
    assert client.get(f"/jobs/{persistent_job_id}/artifacts").status_code == 200

    second_current = _create_job()
    second_job_id = second_current["job_id"]
    assert json.loads(current_manifest_path.read_text(encoding="utf-8"))["job_id"] == second_job_id

    # Default runs overwrite the "current" artifact location.
    assert client.get(f"/jobs/{first_job_id}/artifacts").status_code == 404
    # Dataset-scoped artifacts stay available after later "current" runs.
    assert client.get(f"/jobs/{persistent_job_id}/artifacts").status_code == 200
