# Dataset Interpreter

A monorepo for an AI Data Understanding System designed to demonstrate Forward Deployed Engineer-style system design.

## Repository Structure

- `backend/`: FastAPI backend and data-understanding pipeline services
- `frontend/`: Minimal frontend (not implemented yet)

## Backend Setup (Poetry)

From `backend/`:

```bash
poetry install
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

## API Keys and Env Setup

Store secrets in a gitignored repo-level file:

`/Users/richardwuebker/Projects/workbench/dataset-interpreter/.env/backend.env`

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

Load secrets before running backend:

```bash
set -a
source ../.env/backend.env
set +a
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

The backend exposes:

- `GET /health`
- `POST /jobs/create`
- `GET /jobs/{job_id}`

## Local Demo With Portfolio Frontend

The interactive demo is intentionally localhost-only for security (to avoid exposing paid API usage publicly).

1. Start backend:
```bash
cd /Users/richardwuebker/Projects/workbench/dataset-interpreter/backend
set -a
source ../.env/backend.env
set +a
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

2. Start frontend:
```bash
cd /Users/richardwuebker/Projects/workbench/rwuebker.github.io
npm run dev
```

3. Open:
```text
http://localhost:3000/projects/dataset-interpreter/demo
```

Optional frontend override (if needed):

```bash
# /Users/richardwuebker/Projects/workbench/rwuebker.github.io/.env.local
NEXT_PUBLIC_DATASET_INTERPRETER_API_URL=http://127.0.0.1:8011
```
