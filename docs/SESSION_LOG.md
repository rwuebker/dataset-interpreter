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
- Completed Day 6 profiling enhancements with additional metrics:
  - per-column cardinality (`unique_count`, `unique_percent`)
  - numeric distribution snapshots (`p10`, `p25`, `p50`, `p75`, `p90`, `std`)
  - top values for each column (up to 5 entries)
- Added profiling tests for both real CSV profiling and simulated fallback path.
- Implemented Day 7 issue detection with real dataset checks:
  - missing-data severity
  - duplicate-row detection
  - basic IQR-based numeric outlier detection
  - mixed-type inconsistency detection
- Updated orchestrator to pass ingestion context into issue detection.
- Added issue-detection tests for real CSV checks and profile-only fallback mode.
- Added Day 8 issue prioritization refinement:
  - `severity_score` for each issue
  - `prioritized_issues` sorted by severity for easier downstream UX rendering
- Verified expanded backend test suite passes (`10 passed`).
- Completed Day 9 pipeline integration polish:
  - added `stage_history` tracking in pipeline summary
  - added configurable failure simulation control (`SIMULATE_JOB_FAILURE_PROBABILITY`)
  - improved failed-job payloads to include pipeline summary and stage history
- Verified backend tests remain stable (`10 passed`).

## Next Planned Work
- Begin Day 10 OpenAI interpretation integration with grounded prompt + deterministic fallback.
