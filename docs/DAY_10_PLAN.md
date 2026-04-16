# Day 10 Plan - AI Interpretation Initial (OpenAI)

## Day Goal
Integrate OpenAI to generate grounded interpretation from computed outputs.

## Frontend
- Add "AI Interpretation" section with expandable subsections:
  - dataset purpose
  - likely ML task
  - key issues

## Backend
- Implement `llm_client.py` using OpenAI API.
- Implement first real `ai_interpretation_service.py` prompt pipeline.
- Input to model must include only computed profile/issues and metadata.
- Add fallback behavior if LLM call fails.

## Prompting Requirements
- Force grounded output format (JSON-first response contract).
- Avoid generic advice by referencing concrete stats.

## Needed From You Today
- OpenAI API key.
- Preferred OpenAI model for this project (recommend current fast reasoning model).
- Budget guidance for API usage during development.

## Acceptance Criteria
- AI interpretation endpoint path works in full job run.
- Output clearly references real computed stats.
- Failures degrade gracefully without crashing the job system.
