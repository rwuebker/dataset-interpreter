# Day 02 Plan - Async Job System

## Day Goal
Deliver a clear async orchestration pattern that simulates distributed processing.

## Frontend
- Add simple job creation form placeholder in `frontend/`.
- Add a basic status card area showing job id, status, stage, and progress.
- Keep UI static-first; wire-up can be minimal.

## Backend
- Finalize `POST /jobs/create` request validation (Kaggle-only now).
- Finalize `GET /jobs/{job_id}` response shape.
- Ensure lifecycle transitions:
  - `pending`
  - `running`
  - `completed`
- Ensure stage updates:
  - `ingestion`
  - `profiling`
  - `issue_detection`
  - `interpretation`
- Keep stubbed result payload interview-friendly.

## Testing
- Add API tests for health and job lifecycle.
- Add test for CSV mode returning `501` placeholder response.

## Needed From You Today
- Confirm max poll interval you want frontend to use (recommend 1-2 seconds).
- Confirm whether failed jobs should include internal trace details or user-safe messages only.

## Acceptance Criteria
- Jobs are created instantly and complete asynchronously.
- Polling endpoint returns stable schema fields:
  - `job_id`, `status`, `current_stage`, `progress`, `result`, `error`, `created_at`, `updated_at`.
- Tests pass in backend.

## Validation Commands
```bash
cd backend
poetry run pytest
curl -s -X POST http://127.0.0.1:8000/jobs/create \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"kaggle","kaggle":{"competition":"titanic"}}'
```
