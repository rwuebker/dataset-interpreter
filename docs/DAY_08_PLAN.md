# Day 08 Plan - Issue Detection Refinement

## Day Goal
Improve signal quality so issue outputs are prioritized and actionable.

## Frontend
- Add sorting and grouping for issues by severity.
- Add a top-3 "Most Important Fixes" summary panel.

## Backend
- Enhance issue logic:
  - type inconsistency detection (mixed numeric/text)
  - improved outlier thresholds
  - likely leakage flags (basic heuristic)
- Add ranking algorithm for issue prioritization.
- Include confidence score per issue.

## Testing
- Add synthetic fixtures for type-mismatch and outlier edge cases.
- Ensure deterministic ordering of issues.

## Needed From You Today
- Confirm if you want leakage heuristic included in v1 output.
- Confirm confidence scale format (0-1 float recommended).

## Acceptance Criteria
- Issues are ranked and easier to action.
- Top findings are stable across repeated runs.
