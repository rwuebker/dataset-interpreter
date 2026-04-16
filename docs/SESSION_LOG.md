# Session Log

## 2026-04-14
- Established single-monorepo structure (`dataset-interpreter/` with `backend/` and `frontend/`).
- Implemented FastAPI backend skeleton under `backend/app` with modular architecture.
- Added async job endpoints and in-memory job store with lock-based updates.
- Implemented simulated stage progression (`ingestion`, `profiling`, `issue_detection`, `interpretation`).
- Initialized Poetry inside `backend/` and generated `pyproject.toml` + `poetry.lock`.
- Installed core dependencies (`fastapi`, `uvicorn`, `pandas`, `numpy`) and dev dependencies (`pytest`, `httpx`).
- Added initial docs for roadmap, checkpoints, and testing strategy.
- Added initial backend API tests for health and job lifecycle.

## 2026-04-15
- Added real Kaggle ingestion implementation path (behind `ENABLE_REAL_KAGGLE_INGESTION` flag).
- Implemented Kaggle client wrapper with clear unauthorized/download error translation.
- Added zip extraction and primary CSV selection utilities (`train.csv` preference, fallback largest CSV).
- Expanded backend config with environment-driven settings for storage path and Kaggle credentials.
- Hardened background orchestration to mark jobs as `failed` on runtime exceptions.
- Added secure local-secret workflow using gitignored `/.env/` folder and tracked `backend/.env.example`.
- Updated project ignore rules to prevent committing secrets while keeping safe templates tracked.
- Added Kaggle dependency and aligned Python requirement to `^3.11` for SDK compatibility.
- Resolved local pytest instability by disabling capture plugin in config and verified tests pass.
- Ran live Kaggle ingestion smoke test; confirmed current token returns `401 Unauthorized` for competition download.

## Next Planned Work
- Complete Day 4 ingestion robustness: metadata extraction (rows, columns, column names) and cleaner ingestion errors.
- Add ingestion-focused tests for metadata and primary-file selection behavior.
