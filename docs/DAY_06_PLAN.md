# Day 06 Plan - Profiling Enhancements

## Day Goal
Improve profile quality to handle messy real-world data better.

## Frontend
- Improve profile formatting with grouped sections:
  - numeric columns
  - categorical columns
  - date-like columns
- Add simple density indicator for missingness severity.

## Backend
- Add enhanced profiling metrics:
  - cardinality per column
  - top values for categorical columns
  - approximate distribution summaries for numerics
- Add date parsing attempts and fallback handling.
- Normalize output formatting for predictable downstream prompts.

## Quality and Testing
- Add fixture-driven tests for mixed-type columns.
- Add tests for date-like columns and sparse columns.

## Needed From You Today
- Confirm if date inference should be strict or permissive.
- Confirm whether to include sample raw values in result payload.

## Acceptance Criteria
- Profiling remains fast and stable on larger tables.
- Enhanced metrics are returned without breaking existing schema.
