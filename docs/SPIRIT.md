# SPIRIT.md

## Purpose of This Project

This project uses a Forward Deployed Engineering mindset to solve a real-world problem: how to organize data.

It is not just a coding exercise. It is a simulation of real-world engineering work, where the problem is ambiguous, the data is messy, and the goal is to deliver a working system that helps users make decisions.

This project is designed to answer the question:

“Can you take an unknown dataset, understand it, diagnose issues, and guide what to do next?”

---

## What This Project Is (and Is Not)

### This IS:
- A system that ingests unknown datasets (Kaggle or CSV)
- A pipeline that profiles, diagnoses, and interprets data
- An AI-assisted tool that explains what the data represents
- A system that prepares data for modeling
- A demonstration of:
  - system design
  - modular architecture
  - async processing
  - explainable AI

### This is NOT:
- An AutoML platform
- A deep learning system
- A production-scale distributed system
- A Kaggle competition solver

---

## Core Idea

This system acts like a smart analyst:

1. You give it a dataset (often messy or unknown)
2. It determines:
   - what the dataset is about
   - what type of ML problem it represents
   - what is wrong with the data
3. It explains:
   - what matters
   - what should be fixed
   - what to do next
4. It produces a cleaned, usable dataset for modeling

Everything is:
- structured
- explainable
- grounded in actual computed statistics

---

## Why This Matters for FDE Roles

Forward Deployed Engineers:

- work with messy, real-world data
- solve ambiguous problems
- design systems under constraints
- integrate AI into workflows
- explain results to stakeholders

This project demonstrates all of those skills in a contained, testable way.

---

## System Overview

The system is built as a modular pipeline:

1. Ingestion
   - Pull dataset from Kaggle via API OR accept CSV
   - Extract and select primary dataset (e.g. train.csv)

2. Profiling
   - Infer column types
   - Compute missingness
   - Generate summary statistics

3. Issue Detection
   - Missing data analysis
   - Duplicate detection
   - Outlier detection
   - Type inconsistencies

4. AI Interpretation
   - What the dataset represents
   - Likely ML problem (classification/regression)
   - Key risks and issues
   - Suggested next steps

5. Optional Cleaning
   - Apply basic fixes:
     - imputation
     - type correction
     - duplicate removal
   - Output a model-ready dataset

---

## Architecture Philosophy

This project reflects real system design principles:

- Clear separation of concerns (services layer)
- Async job orchestration (simulating distributed systems)
- Minimal, testable components
- No overengineering

Even though it runs as a single service, it is structured so it could be split into:

- ingestion workers
- profiling workers
- issue detection workers
- AI interpretation services

---

## Async Job Model

All work is executed via an async job system:

- User submits dataset → job created
- System processes stages:
  - ingestion
  - profiling
  - issue_detection
  - interpretation
- User polls for results

This simulates:
- background processing
- job queues
- long-running workflows

---

## Kaggle Integration

Kaggle is used because:

- datasets are real and widely recognized
- they provide structured but imperfect data
- they simulate real-world ML scenarios

The system will:

- download datasets via Kaggle API
- extract files
- select the primary dataset (prefer train.csv)
- analyze it without manual intervention

---

## Two-Week Execution Plan

This project is built over 14 days with iterative delivery.

### Week 1: System Foundation

Day 1–2
- FastAPI setup
- async job system
- job store and lifecycle

Day 3–4
- dataset ingestion (Kaggle)

Day 5–6
- profiling system

Day 7
- issue detection (initial)

---

### Week 2: Intelligence + Polish

Day 8–9
- improve issue detection

Day 10–11
- AI interpretation (LLM integration)

Day 12
- dataset cleaning + output

Day 13
- refine explanations and outputs

Day 14
- documentation + demo readiness

---

## Design Constraints

To maintain focus:

- No Kubernetes
- No distributed infrastructure
- No deep learning
- No full AutoML
- No overengineering

The goal is clarity, not complexity.

---

## Success Criteria

The project is successful if:

- A user can input a Kaggle dataset
- The system runs asynchronously
- The system returns:
  - dataset profile
  - detected issues
  - AI-generated explanation
  - optionally a cleaned dataset

Most importantly:

The system clearly explains what the data is and what should be done next.

---

## Final Note

This project is not about building the most complex system.

It is about demonstrating:

- how to think
- how to design
- how to deliver

under real-world constraints.

That is what gets you hired as a Forward Deployed Engineer.
