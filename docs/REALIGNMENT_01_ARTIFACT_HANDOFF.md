# Realignment 01: Artifact-First Dataset Handoff System

## Date
- 2026-04-20

## Why This Realignment Exists
Dataset Interpreter v1 proved the core pipeline works:
- async job orchestration
- Kaggle ingestion
- profiling
- issue detection
- AI interpretation
- optional cleaning

However, v1 output experience is still centered on a large raw JSON response. For Forward Deployed Engineer positioning, the system now needs to evolve into:

- a human-readable decision-support report
- a machine-readable handoff contract for downstream services

This realignment turns Dataset Interpreter into a "dataset handoff layer" between raw Kaggle inputs and downstream modeling/feature-engineering systems.

## Product Statement (Aligned)
"Take a Kaggle competition dataset, interpret it, diagnose it, clean/prep it, and emit a human-readable report plus machine-readable artifacts for downstream modeling or feature-engineering services."

## Scope of This Realignment
This realignment is backend-first.

### In scope now
- versioned artifact package generation
- manifest contract
- summary and artifact retrieval endpoints
- deterministic modeling contract generation
- deterministic feature cards generation (JSONL)
- cleaning plan vs cleaning receipt separation
- lightweight Kaggle multi-file awareness metadata
- no absolute local filesystem paths in public API responses

### Out of scope for now
- complex feature drilldown UI
- multi-table join inference
- AutoML/deep learning
- distributed infra additions (Kafka/Celery/K8s)
- per-feature LLM calls

## Existing System To Preserve
The following are already implemented and must continue to work:
- `GET /health`
- `POST /jobs/create`
- `GET /jobs/{job_id}`
- async lifecycle and stage history
- in-memory job store
- existing services and tests

No breaking changes to existing endpoints are allowed in this realignment.

## Artifact Package (Required)
For each completed job, generate:

`backend/data/artifacts/<job_id>/`
- `manifest.json`
- `dataset_report.json`
- `data_profile.json`
- `issue_report.json`
- `interpretation.json`
- `feature_cards.jsonl`
- `cleaning_plan.json`
- `cleaning_receipt.json`
- `modeling_contract.json`
- `cleaned_train.csv` (only if cleaning output enabled and produced)

## Public API Path Rule
Public API payloads must not expose local absolute file paths such as `/Users/...`.

Public responses should expose:
- `artifact_id`
- `filename`
- `content_type`
- `download_url`

Internal filesystem paths are allowed only inside backend internals.

## Manifest Contract
`manifest.json` includes one record per artifact:
- `artifact_id`
- `filename`
- `content_type`
- `description`
- `schema_version` (when applicable)
- `download_url`
- `created_at`

Suggested artifact IDs:
- `manifest`
- `dataset_report`
- `data_profile`
- `issue_report`
- `interpretation`
- `feature_cards`
- `cleaning_plan`
- `cleaning_receipt`
- `modeling_contract`
- `cleaned_train_csv`

## New Endpoints (Required)
Add without breaking current endpoints:

- `GET /jobs/{job_id}/summary`
- `GET /jobs/{job_id}/artifacts`
- `GET /jobs/{job_id}/artifacts/{artifact_id}`

### Summary endpoint intent
Compact, human-oriented frontend payload:
- `job_id`
- `status`
- `source`
- `competition`
- `selected_file`
- `rows`
- `columns`
- `inferred_problem_type`
- `inferred_target_column`
- `readiness_label` / `readiness_score`
- `top_issues`
- `recommended_next_steps`
- artifact links

### Artifacts endpoint intent
Return manifest object for completed job.

### Single artifact endpoint intent
Return/download one artifact by `artifact_id`.
- JSON -> `application/json`
- JSONL -> `application/jsonl` (or `text/plain` fallback)
- CSV -> `text/csv`

## Modeling Contract (Required)
`modeling_contract.json` schema version:
- `dataset_interpreter.modeling_contract.v1`

It must include:
- job metadata
- source metadata
- selected file
- inferred problem type
- inferred target column
- target confidence
- metric hint
- column roles:
  - id columns
  - target columns
  - numeric features
  - categorical features
  - boolean features
  - high-cardinality categoricals
  - excluded-by-default columns
- quality gates
- recommended preprocessing
- artifact links

### Titanic expectation (approximate)
- problem type: `binary_classification`
- target: `Survived`
- id columns: `PassengerId`
- excluded by default includes `PassengerId`
- high-cardinality categoricals include `Name`, `Ticket`, `Cabin`

## Feature Cards (Required)
`feature_cards.jsonl`:
- one JSON object per column
- deterministic from profile + issues outputs
- no per-feature LLM calls

Each card includes:
- `column`
- `role`
- `physical_type`
- `semantic_type`
- `missing_percent`
- `unique_count`
- `unique_percent`
- `quality_status`
- `recommended_action`
- `use_in_model`
- `rationale`

Optional, if cheap:
- numeric distribution from existing profile stats
- categorical top values from existing profile stats

## Cleaning Plan vs Cleaning Receipt
These are distinct artifacts:

- `cleaning_plan.json`: what should be done and why
- `cleaning_receipt.json`: what was actually done

Important policy note for Titanic:
- Do not present raw `Cabin` mode-imputation as the preferred plan with ~77% missingness.
- Prefer deriving `has_cabin` indicator and/or excluding raw `Cabin` by default.

## Kaggle Multi-file Awareness (Lightweight)
No joins yet. Add metadata awareness only when available:
- `files_detected`
- `selected_train_file`
- `selected_test_file`
- `sample_submission_file`

Known filename patterns:
- `train.csv`
- `test.csv`
- `sample_submission.csv`
- `gender_submission.csv`

Optional heuristic:
- if a column exists in train + sample_submission but not test, it is a likely target candidate.

## Orchestrator Integration Rule
Artifact generation executes after:
- ingestion
- profiling
- issue_detection
- interpretation
- optional cleaning

and before marking job completed.

Adding a new stage label may be deferred if invasive; keep current stage behavior stable first.

## Frontend Direction (Deferred)
Frontend redesign comes after backend artifact system is in place.
Target sections later:
1. Input
2. Pipeline Status
3. Executive Summary
4. Data Quality Cards
5. Feature Explorer Table
6. Feature Drilldown Side Panel
7. AI Interpretation
8. Artifact Downloads
9. Raw JSON (collapsed)

## Implementation Sequence (Approved)
1. Artifact manifest generation
2. Artifact endpoints
3. Modeling contract
4. Feature cards
5. Cleaning plan/receipt split
6. Frontend report layout

## Test Expectations
Add/extend tests for:
1. artifact package creation
2. manifest completeness
3. summary endpoint
4. artifacts endpoint
5. artifact download endpoint with proper content types
6. modeling contract role inference on Titanic-like fixture
7. feature cards row count and schema keys
8. no `/Users/...` in public API responses
9. existing `GET /jobs/{job_id}` still works

## Acceptance Criteria Snapshot
Using Titanic:
1. submit job
2. wait for completion
3. call summary endpoint
4. call artifacts endpoint
5. download modeling contract
6. download feature cards
7. download cleaning plan
8. download cleaning receipt
9. download cleaned CSV when enabled
10. verify no absolute local paths in public responses
11. verify existing job endpoint behavior remains intact

## Risks and Guardrails
- Risk: accidental path leakage in existing `GET /jobs/{job_id}` payload.
  - Guardrail: sanitize artifact-facing fields in public responses.
- Risk: over-expanding scope into frontend before backend contracts stabilize.
  - Guardrail: backend-first implementation order.
- Risk: nondeterministic outputs reducing downstream reliability.
  - Guardrail: deterministic rules for modeling contract and feature cards.

## Definition of Done for Realignment 01 (Backend)
- Artifact package generated for completed jobs.
- New endpoints available and tested.
- Modeling contract + feature cards + cleaning plan/receipt artifacts present.
- Public responses use artifact references (not local absolute paths).
- Existing endpoints and pipeline behavior remain stable.
