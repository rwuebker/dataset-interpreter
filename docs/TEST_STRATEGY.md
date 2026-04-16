# Test Strategy

## Principles
- keep tests close to behavior that matters for interviews
- prioritize service contracts and job orchestration correctness
- prefer deterministic tests over brittle timing-only checks

## Test Layers

### 1) API Contract Tests
- validate endpoint status codes and response payload shape
- validate unsupported modes (e.g., CSV placeholder) return expected errors

### 2) Orchestration Tests
- verify stage ordering and job state progression
- verify final payload is assembled when pipeline succeeds
- later: verify failure path and error payload contract

### 3) Service Unit Tests (incremental)
- ingestion selection logic (`train.csv` preference)
- profiling metrics correctness
- issue detection heuristics on known fixtures

## Current Test Commands
From `backend/`:

```bash
poetry run pytest
```

## Near-Term Additions
- fixture-based tests for messy datasets
- simulated failure tests for each stage
- snapshot-like checks for interview-friendly response structure
