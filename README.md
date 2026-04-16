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

The backend exposes:

- `GET /health`
- `POST /jobs/create`
- `GET /jobs/{job_id}`
