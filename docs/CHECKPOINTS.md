# Execution Checkpoints

## Checkpoint 1: Skeleton Ready (Target: Day 2)
Definition of done:
- backend app runs with Poetry
- endpoints live: `/health`, `/jobs/create`, `/jobs/{job_id}`
- async stage progression simulated
- basic tests green for health + job lifecycle

Interview value:
- demonstrates modular API/service/store split
- demonstrates async orchestration pattern used in distributed systems

## Checkpoint 2: Real Ingestion (Target: Day 4)
Definition of done:
- Kaggle competition ingestion implemented
- zip extraction and primary dataset selection (`train.csv` preferred)
- ingestion outputs metadata used by downstream services

Interview value:
- demonstrates handling of external systems and messy file conventions

## Checkpoint 3: Real Profiling + Issues (Target: Day 8)
Definition of done:
- profiling service computes real column and quality stats
- issue detection returns prioritized, explainable findings
- tests cover messy synthetic datasets

Interview value:
- demonstrates decision-support logic on unknown data

## Checkpoint 4: Grounded AI Interpretation (Target: Day 10)
Definition of done:
- LLM abstraction integrated
- interpretation grounded in computed profile/issues
- output includes ML framing and next-step guidance

Interview value:
- demonstrates practical and explainable LLM integration

## Checkpoint 5: Demo-Ready End-to-End (Target: Day 14)
Definition of done:
- end-to-end run from Kaggle input to interpreted output
- docs and runbook complete
- tests and smoke checks stable

Interview value:
- demonstrates production thinking, reliability, and delivery discipline
