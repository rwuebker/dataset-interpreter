# Day 11 Plan - AI Interpretation Refinement

## Day Goal
Upgrade interpretation quality so outputs are useful for stakeholder decisions.

## Frontend
- Improve readability with structured cards:
  - summary
  - risks
  - recommended next steps
- Add copy-to-markdown button for interview demo usage.

## Backend
- Refine prompt strategy for consistency and clarity.
- Add response validation for required sections.
- Add explicit outputs:
  - likely problem type (classification/regression)
  - top 3 risks
  - prioritized next actions
- Add optional deterministic templated fallback when LLM confidence is low.

## Quality
- Add regression tests for output schema integrity.
- Add fixtures to validate grounding statements against known stats.

## Needed From You Today
- Confirm voice/tone preference for generated summaries (technical vs executive).
- Confirm max output length for API responses.

## Acceptance Criteria
- Interpretation quality is clear, grounded, and consistent.
- Output is demo-ready without manual editing.
