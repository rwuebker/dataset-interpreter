from datetime import datetime, timezone
from threading import RLock

from app.schemas.job import JobRecord


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = RLock()

    def create(self, job: JobRecord) -> JobRecord:
        with self._lock:
            self._jobs[job.job_id] = job
            return job

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields: object) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None

            updated = job.model_copy(
                update={
                    **fields,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._jobs[job_id] = updated
            return updated


job_store = JobStore()
