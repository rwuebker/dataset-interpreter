# Dataset Interpreter 14-Day Execution Plan

## Week 1: Core Backend System

### Day 1
- finalize backend skeleton and Poetry environment
- confirm async job endpoints (`POST /jobs/create`, `GET /jobs/{job_id}`, `GET /health`)
- ensure clean modular structure under `backend/app`

### Day 2
- harden job lifecycle behavior (`pending -> running -> completed/failed`)
- add stage and progress updates for each pipeline phase
- add basic automated API tests for job creation and polling

### Day 3
- implement Kaggle ingestion client wrapper and service interface
- download competition files to local working directory
- extract dataset zip and add safe file-selection utility

### Day 4
- add primary dataset selection logic (`train.csv` preference)
- add ingestion metadata output (row hints, file selected, source info)
- add ingestion failure handling and explicit error reporting

### Day 5
- implement profiling service (column types, missing values, basic stats)
- build compact profile schema for downstream issue detection and LLM input

### Day 6
- improve profiling robustness for messy columns (mixed types, date detection)
- add tests for profile outputs on synthetic messy CSV fixtures

### Day 7
- implement issue detection service: missingness severity, duplicates, outliers, type inconsistencies
- produce prioritized issue list with severity and actionability

## Week 2: Interpretation, UX Readiness, Demo Readiness

### Day 8
- refine issue detection thresholds and make config-driven where needed
- add issue detection tests for edge cases

### Day 9
- implement LLM client abstraction and ai interpretation service
- generate grounded interpretation from computed profile/issues only

### Day 10
- tighten AI output schema (dataset meaning, likely ML problem, top risks, next steps)
- add deterministic fallback behavior when LLM is unavailable

### Day 11
- improve API result payload for demo readability
- add job error examples and clearer status transitions for interview walkthroughs

### Day 12
- add endpoint-level smoke scripts and docs for local runs
- align outputs for “decision-support analyst” narrative

### Day 13
- integration pass across all services
- add final test sweep and regressions for main flow

### Day 14
- final polish: README, architecture diagram, deployment notes (Render backend)
- prepare demo script and interview talking points
