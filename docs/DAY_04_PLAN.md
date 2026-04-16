# Day 04 Plan - Ingestion Robustness and Metadata

## Day Goal
Make ingestion dependable and informative for downstream services.

## Frontend
- Show ingestion block in results:
  - competition
  - selected file
  - row/column count preview
- Add user-friendly error display for ingestion failures.

## Backend
- Harden file extraction and directory hygiene.
- Add metadata collection:
  - row count
  - column count
  - column names
  - inferred delimiter info
- Add explicit ingestion error cases:
  - bad competition
  - auth failure
  - no CSV files found
- Ensure errors map to `job.status=failed` and `job.error`.

## Ops and Config
- Add configurable data paths in `core/config.py`.
- Add safe cleanup behavior for repeated runs.

## Needed From You Today
- Confirm retention behavior:
  - keep all downloaded data
  - or cleanup old runs after N days.
- Confirm whether sample datasets may be committed for tests.

## Acceptance Criteria
- Ingestion succeeds on known Kaggle sample.
- Failed ingestion surfaces actionable error reason.
- Metadata appears in result payload for next services.
