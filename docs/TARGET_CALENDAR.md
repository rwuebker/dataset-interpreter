# 14-Day Build Plan: Dataset Interpreter (FDE Demo Project)

Goal:
Ship a complete, demo-ready system in 14 days that:
- ingests Kaggle datasets
- analyzes and diagnoses data quality
- explains dataset purpose and ML usage
- optionally outputs a cleaned dataset
- demonstrates strong system design + async workflows + AI integration

Each day is split into:
1. Frontend (lightweight, demo-focused)
2. Backend (primary focus)

---

## Day 1 – Project Setup & Skeleton

Frontend:
- Create basic project folder inside /frontend
- Add simple index.html placeholder (title + “Dataset Interpreter”)
- Plan minimal UI (no real functionality yet)

Backend:
- Initialize FastAPI app with Poetry
- Create project structure (app/, api/, services/, etc.)
- Implement /health endpoint
- Create basic job store + schemas
- Ensure app runs locally

Big Picture:
Establish a clean, runnable foundation.

---

## Day 2 – Async Job System

Frontend:
- Add simple UI for “Create Job” (form placeholder)
- Add placeholder for job status display

Backend:
- Implement POST /jobs/create
- Implement GET /jobs/{job_id}
- Add BackgroundTasks for async processing
- Simulate job lifecycle (pending → running → completed)
- Add stage tracking (ingestion → profiling → etc.)

Big Picture:
Demonstrate async system behavior (key FDE signal).

---

## Day 3 – Kaggle Ingestion (Basic)

Frontend:
- Add input field for Kaggle competition name
- Hook form to backend API

Backend:
- Implement Kaggle API integration
- Download dataset zip
- Extract files
- Select primary dataset (train.csv)
- Return basic dataset metadata

Big Picture:
System can pull real-world data automatically.

---

## Day 4 – Ingestion Stability & Metadata

Frontend:
- Display ingestion results (dataset name, file selected)
- Improve basic UI feedback

Backend:
- Improve ingestion robustness (file handling, paths)
- Add dataset metadata output (rows, columns, column names)
- Handle ingestion errors cleanly

Big Picture:
Reliable data ingestion with clear outputs.

---

## Day 5 – Profiling System (Core Stats)

Frontend:
- Display basic dataset profile (table preview, column list)

Backend:
- Implement profiling_service:
  - column types
  - missing values
  - summary stats
- Return structured profile data

Big Picture:
System understands dataset structure.

---

## Day 6 – Profiling Enhancements

Frontend:
- Improve visualization of profile (simple tables or sections)

Backend:
- Add deeper stats:
  - distributions (basic)
  - cardinality
- Clean output formatting

Big Picture:
Make profiling useful and readable.

---

## Day 7 – Issue Detection (Initial)

Frontend:
- Add “Detected Issues” section

Backend:
- Implement issue_detection_service:
  - missing data severity
  - duplicate detection
  - basic outlier detection
- Return structured issue list

Big Picture:
System begins diagnosing problems.

---

## Day 8 – Issue Detection (Refinement)

Frontend:
- Improve issue display (grouped, readable)

Backend:
- Enhance issue detection:
  - type inconsistencies
  - better outlier logic
- Prioritize issues (severity ranking)

Big Picture:
Move from raw detection → meaningful insights.

---

## Day 9 – Pipeline Integration

Frontend:
- Show full pipeline output (profile + issues)

Backend:
- Integrate ingestion + profiling + issue detection in orchestrator
- Ensure stage transitions are correct
- Ensure full pipeline runs cleanly

Big Picture:
End-to-end pipeline (without AI yet).

---

## Day 10 – AI Interpretation (Initial)

Frontend:
- Add “AI Interpretation” section

Backend:
- Integrate LLM client
- Generate explanation:
  - dataset purpose
  - ML problem type
- Use profiling + issues as input

Big Picture:
System starts “thinking,” not just computing.

---

## Day 11 – AI Interpretation (Refinement)

Frontend:
- Improve readability of AI output (sections, formatting)

Backend:
- Improve prompt design
- Ensure explanations are grounded in real stats
- Add:
  - key risks
  - suggested next steps

Big Picture:
High-quality, useful explanations (major differentiator).

---

## Day 12 – Data Cleaning Output

Frontend:
- Add “Download Cleaned Dataset” button (basic)

Backend:
- Implement simple cleaning:
  - imputation
  - duplicate removal
  - type fixes
- Output cleaned dataset file

Big Picture:
System produces actionable output.

---

## Day 13 – Polish & UX

Frontend:
- Clean layout (sections: input, status, results)
- Improve loading states and status updates

Backend:
- Improve error handling
- Ensure all responses are clean and consistent
- Add logging (basic)

Big Picture:
Make the system demo-ready and smooth.

---

## Day 14 – Finalization & Demo Prep

Frontend:
- Final UI polish
- Ensure demo flow is smooth and fast

Backend:
- Final cleanup
- Ensure deployment readiness (Render)
- Validate full pipeline on at least 1–2 Kaggle datasets

Big Picture:
Ready to demo:
- input dataset
- run job
- show full interpretation
- explain system design

---

## Final Outcome

By Day 14, you have:

- A working AI system that:
  - ingests real data
  - analyzes it
  - explains it
  - prepares it for modeling

- A clean architecture you can explain

- A strong demo for FDE roles

This is not about perfection.
This is about delivering a complete, thoughtful system under constraints.
