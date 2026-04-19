# Dataset Interpreter

A monorepo for an AI Data Understanding System designed to demonstrate Forward Deployed Engineer-style system design.

## Repository Structure

- `backend/`: FastAPI backend and data-understanding pipeline services
- `frontend/`: Local demo frontend (static HTML/JS)

## Prerequisites

- Python `3.11+`
- Poetry

## API Keys and Env Setup

Store secrets in a gitignored repo-level file:

`./.env/backend.env`

Required keys:

- `OPENAI_API_KEY`: used for AI interpretation stage.
- `KAGGLE_USERNAME`: Kaggle account username for dataset download.
- `KAGGLE_KEY`: Kaggle API token paired with the username.

Recommended runtime toggles:

- `ENABLE_REAL_AI_INTERPRETATION=true`
- `ENABLE_REAL_KAGGLE_INGESTION=true`
- `ENABLE_CLEANING_OUTPUT=true`
- `SIMULATE_JOB_FAILURE_PROBABILITY=0.0`

Template:

```bash
mkdir -p .env
cat > .env/backend.env <<'EOF'
OPENAI_API_KEY=your_openai_api_key
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key
ENABLE_REAL_AI_INTERPRETATION=true
ENABLE_REAL_KAGGLE_INGESTION=true
ENABLE_CLEANING_OUTPUT=true
SIMULATE_JOB_FAILURE_PROBABILITY=0.0
EOF
```

Important:

- Never put real secrets in tracked files like `.env.example`.
- Never commit `.env/backend.env` to GitHub.

## Run Locally (Self-Contained)

1. Start backend:

```bash
cd backend
poetry install
set -a
source ../.env/backend.env
set +a
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

2. Start frontend (from this repo):

```bash
cd frontend
python3 -m http.server 3000
```

3. Open:

```text
http://127.0.0.1:3000
```

4. In the UI prompt, enter either:

- Kaggle competition slug (example: `titanic`)
- Full Kaggle competition URL (example: `https://www.kaggle.com/competitions/titanic/overview`)

The frontend normalizes URL input to the required slug automatically.

## API Endpoints

- `GET /health`
- `POST /jobs/create`
- `GET /jobs/{job_id}`

## Where Kaggle Data Is Stored

When `ENABLE_REAL_KAGGLE_INGESTION=true`, downloads are written under:

- `backend/data/raw/<competition_slug>/<timestamp>_<short_id>/download`
- `backend/data/raw/<competition_slug>/<timestamp>_<short_id>/extracted`

If cleaning is enabled, cleaned output is saved under:

- `backend/data/raw/<competition_slug>/<timestamp>_<short_id>/cleaned`

If `ENABLE_REAL_KAGGLE_INGESTION=false`, ingestion is simulated and no Kaggle files are downloaded.

## Kaggle Download Caching

Real Kaggle raw downloads are cached by competition slug so we do not repeatedly consume Kaggle download quota.

- First time for a slug:
  - download Kaggle zip once
  - extract once
- Later jobs for the same slug:
  - skip download
  - reuse cached extracted raw CSVs
  - run profiling/issue detection/AI interpretation on cached raw data

Cache location:

- `backend/data/raw/<competition_slug>/raw_cache/download`
- `backend/data/raw/<competition_slug>/raw_cache/extracted`

Per-job outputs (for isolated artifacts like cleaning output) still use unique run folders:

- `backend/data/raw/<competition_slug>/<timestamp>_<short_id>/`
