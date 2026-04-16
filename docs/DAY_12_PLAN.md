# Day 12 Plan - Optional Cleaning Output

## Day Goal
Produce an optional cleaned dataset artifact for immediate modeling use.

## Frontend
- Add "Generate Cleaned Dataset" action.
- Add link/button for cleaned artifact download when available.

## Backend
- Implement optional cleaning stage:
  - imputation (simple defaults)
  - duplicate removal
  - basic type correction
- Persist cleaned dataset path in job result.
- Keep original and cleaned versions traceable.

## Data Governance
- Include cleaning summary with counts of rows/fields changed.
- Ensure non-destructive workflow.

## Needed From You Today
- Confirm cleaning defaults (mean/median/mode by type).
- Confirm whether cleaned artifacts should be retained or auto-expired.

## Acceptance Criteria
- Cleaned dataset is generated for supported inputs.
- Job result includes artifact path + cleaning summary.
