# Demo Runbook

## 1) Start Backend
```bash
cd backend
set -a
source ../.env/backend.env
set +a
poetry run uvicorn app.main:app --reload
```

## 2) Health Check
```bash
curl -s http://127.0.0.1:8000/health
```

## 3) Create Analysis Job
```bash
curl -s -X POST http://127.0.0.1:8000/jobs/create \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"kaggle","kaggle":{"competition":"titanic"}}'
```

## 4) Poll Job Status
```bash
curl -s http://127.0.0.1:8000/jobs/<job_id>
```

## 5) Demo Talking Flow
1. Explain async orchestration and stage lifecycle.
2. Show profile output and key quality metrics.
3. Show prioritized issues with severity scores.
4. Show grounded AI interpretation output.
5. Show optional cleaned dataset artifact metadata.

## Notes
- If Kaggle returns `401 Unauthorized`, verify token scope and competition acceptance.
- For stable demos, use:
  - `SIMULATE_JOB_FAILURE_PROBABILITY=0.0`
  - `ENABLE_REAL_KAGGLE_INGESTION=false` (if Kaggle auth is not ready)
