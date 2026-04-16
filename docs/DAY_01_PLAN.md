# Day 01 Plan - Project Setup and Skeleton

## Day Goal
Stand up a clean monorepo foundation that runs locally and is ready for iterative delivery.

## Frontend
- Keep `frontend/` minimal and non-blocking.
- Add a placeholder `index.html` with project title and short description.
- Document intended future route on `rwuebker.github.io`: `/projects/dataset-interpreter`.

## Backend
- Confirm Poetry config in `backend/` and install dependencies.
- Ensure FastAPI bootstrap exists in `backend/app/main.py`.
- Ensure routers are registered and `GET /health` works.
- Validate skeleton services and job schemas are organized under `backend/app`.
- Confirm in-memory store + async stage simulation are runnable.

## DevOps and Repo
- Initialize Git repo at `dataset-interpreter/`.
- Add `.gitignore` for Python, Node, env files, and local artifacts.
- Set default branch to `main`.

## Needed From You Today
- Confirm canonical GitHub repository URL to push this repo.
- Confirm preferred license (`MIT` recommended).
- Confirm whether `frontend/` will stay plain HTML initially or move to your Next.js app only.

## Acceptance Criteria
- `poetry install` succeeds in `backend/`.
- `poetry run uvicorn app.main:app --reload` starts without errors.
- `GET /health` returns `{ "status": "ok" }`.
- Repo is initialized with clean ignore rules.

## Validation Commands
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
curl -s http://127.0.0.1:8000/health
```

## Risks to Watch
- Missing environment isolation.
- Untracked secrets or local files accidentally committed.
