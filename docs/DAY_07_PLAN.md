# Day 07 Plan - Issue Detection Initial

## Day Goal
Deliver the first practical diagnosis layer over computed profile data.

## Frontend
- Add "Detected Issues" section with severity tags.
- Group issues by type for readability.

## Backend
- Implement initial `issue_detection_service.py` logic:
  - missing data severity
  - duplicate row detection
  - basic outlier detection for numeric columns
- Return issue objects with fields:
  - issue_type
  - severity
  - affected_columns
  - explanation
  - recommended_action

## Testing
- Add unit tests covering each issue type.
- Add end-to-end assertion that issue list appears in job result.

## Needed From You Today
- Confirm severity rubric (`low`, `medium`, `high`, `critical`).
- Confirm whether duplicates should be measured globally or by likely key columns later.

## Acceptance Criteria
- Issue detection returns non-empty findings on messy datasets.
- Severity and explanations are clear and interview-ready.
