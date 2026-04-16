# Dataset Interpreter

A monorepo for an AI Data Understanding System designed to demonstrate Forward Deployed Engineer-style system design.

## Repository Structure

- `backend/`: FastAPI backend and data-understanding pipeline services
- `frontend/`: Minimal frontend (not implemented yet)

## Backend Setup (Poetry)

From `backend/`:

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Local Secrets (Gitignored)

Use a local repo-level folder for keys:

```bash
mkdir -p .env
cat > .env/backend.env <<'EOF'
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key
OPENAI_API_KEY=your_openai_api_key
ENABLE_REAL_KAGGLE_INGESTION=true
EOF
```

Load secrets before running backend:

```bash
set -a
source ../.env/backend.env
set +a
poetry run uvicorn app.main:app --reload
```

The backend exposes:

- `GET /health`
- `POST /jobs/create`
- `GET /jobs/{job_id}`
