# NeuroFlow-HiDevs

NeuroFlow is a modular, production-grade Retrieval-Augmented Generation (RAG) system designed for multi-modal ingestion, hybrid retrieval, evaluation-driven optimization, and adaptive fine-tuning.

## Core Systems
- Ingestion Pipeline (multi-modal)
- Hybrid Retrieval (vector + keyword + metadata)
- LLM Generation with routing
- Evaluation (LLM-as-judge)
- Continuous Fine-Tuning

## Tech Stack (Planned)
- Backend: FastAPI
- Vector Store: pgvector
- DB: PostgreSQL
- Frontend: React
- Infra: Docker + Kubernetes
- ML Tracking: MLflow

## Branch
- `task-31` → Architecture + Contracts

This repo is intentionally designed before implementation to avoid architectural debt.