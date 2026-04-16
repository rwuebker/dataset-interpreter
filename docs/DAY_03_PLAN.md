# Day 03 Plan - Kaggle Ingestion Basic

## Day Goal
Move from simulated ingestion to real Kaggle dataset download and extraction.

## Frontend
- Add Kaggle competition input field.
- Add submit action to call `POST /jobs/create`.
- Show immediate job id after submission.

## Backend
- Implement `kaggle_client.py` wrapper for Kaggle API calls.
- Implement ingestion path handling and zip extraction.
- Select primary dataset file with priority:
  1. `train.csv`
  2. largest CSV
- Return ingestion metadata in job result:
  - source
  - competition
  - selected_file
  - local_dataset_path

## Data Handling Rules
- Single-table dataset only.
- Skip joins and cross-file fusion.
- Fail fast with clear message when no CSV exists.

## Needed From You Today
- Kaggle credentials:
  - `KAGGLE_USERNAME`
  - `KAGGLE_KEY`
- Preferred local storage root for downloaded datasets (recommend `backend/data/raw`).

## Acceptance Criteria
- Kaggle competition name triggers real download.
- Zip extracts successfully.
- Primary CSV is selected automatically.
- Pipeline continues using selected file.

## Validation Commands
```bash
cd backend
poetry run uvicorn app.main:app --reload
curl -s -X POST 'http://127.0.0.1:8000/jobs/create' \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"kaggle","kaggle":{"competition":"titanic"}}'
```
