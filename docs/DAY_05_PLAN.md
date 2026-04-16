# Day 05 Plan - Profiling Core Statistics

## Day Goal
Implement robust profile generation for unknown tabular datasets.

## Frontend
- Add profile section cards:
  - schema overview
  - missingness summary
  - numeric summary table
- Keep display compact and readable.

## Backend
- Implement `profiling_service.py` with real pandas logic.
- Compute:
  - inferred column types
  - missing values (count + percent)
  - basic numeric stats (`min`, `max`, `mean`, `median`)
- Return profile as structured JSON with stable keys.

## Data Contract
- Profile output should be machine-readable and LLM-readable.
- Include concise dataset summary sentence for UI display.

## Needed From You Today
- Confirm if we should treat high-cardinality text columns as categorical or text.
- Confirm max preview rows for frontend display (recommend 20).

## Acceptance Criteria
- Profile runs on real Kaggle-selected CSV.
- Output includes column-level summaries and missingness.
- Schema is stable across datasets.
