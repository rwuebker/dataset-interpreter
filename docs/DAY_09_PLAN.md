# Day 09 Plan - Pipeline Integration and Stability

## Day Goal
Integrate ingestion, profiling, and issue detection into one reliable job flow.

## Frontend
- Show full pipeline status timeline.
- Show combined output sections for profile + issues.

## Backend
- Wire real service outputs in `job_orchestrator.py`.
- Ensure stage transitions map to actual execution boundaries.
- Add controlled failure simulation (~3%) for async realism.
- Ensure failed stage and error message are saved in job response.

## Reliability
- Add timeout safeguards around long-running operations.
- Add minimal retry strategy for transient ingestion failures (if safe).

## Needed From You Today
- Confirm failure simulation should stay enabled in demo mode.
- Confirm whether retries are acceptable for Kaggle downloads.

## Acceptance Criteria
- End-to-end run works without manual intervention.
- Job status and stage reporting are always consistent.
