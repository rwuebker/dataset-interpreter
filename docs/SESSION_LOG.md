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
- Implemented ingestion metadata extraction from selected CSV:
  - `row_count`
  - `column_count`
  - `column_names`
  - `delimiter`
- Added ingestion tests for metadata extraction, `train.csv` primary-file preference, and simulated ingestion metadata output.
- Verified expanded backend test suite passes (`6 passed`).
- Began Day 5 profiling implementation with real computed stats from selected CSV.
- Replaced profiling stub with actual outputs:
  - row/column counts
  - column name list
  - type classification (`numerical`, `categorical`, `boolean`)
  - missing-value summaries
  - numeric min/max/mean/median summaries
- Added profiling tests for both real CSV profiling and simulated fallback path.
- Verified expanded backend test suite passes (`8 passed`).

## Next Planned Work
- Continue Day 5/6 profiling polish and then move into Day 7 issue-detection improvements.
