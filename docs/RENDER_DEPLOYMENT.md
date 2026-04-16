# Render Deployment (Backend)

## Service Type
- Web Service (Python)

## Root Directory
- `backend`

## Build Command
```bash
poetry install --no-root
```

## Start Command
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Required Environment Variables
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (recommended: `gpt-4.1-mini`)
- `ENABLE_REAL_AI_INTERPRETATION` (`true`/`false`)
- `ENABLE_REAL_KAGGLE_INGESTION` (`true`/`false`)
- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `DATASET_STORAGE_ROOT` (default `data/raw`)
- `SIMULATE_STAGE_DELAY_SECONDS` (default `0.6`)
- `SIMULATE_JOB_FAILURE_PROBABILITY` (default `0.0`)
- `ENABLE_CLEANING_OUTPUT` (`true`/`false`)

## Notes
- Keep all secrets in Render environment variables; do not commit keys.
- If Kaggle competition download fails with 401, verify competition access acceptance and API token scope.
- For demo stability, set `SIMULATE_JOB_FAILURE_PROBABILITY=0.0`.
