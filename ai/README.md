# AI Layer (scaffold)

This directory is reserved for the AI Risk Assistant work described in `PRODUCT_BACKLOG.md`
(RAG over risk evidence, tool-enabled agents, multi-agent risk analysis). It is intentionally
empty of working code right now — per the roadmap's own sequencing advice: **add AI only after
the non-AI application works.**

The FastAPI backend (`backend/`) and Next.js frontend (`frontend/`) are the core application and
should stay fully usable without anything in this directory.

## Layout (matches the target architecture)

- `agents/` — one file per agent (`risk_agent.py`, `assessment_agent.py`, `evidence_agent.py`,
  `manager_agent.py`). Built with the OpenAI Agents SDK for Python. The manager agent delegates
  to the specialists; each specialist gets narrow, well-defined tools.
- `tools/` — function-calling tools the agents use to read/write application data (risks, tasks,
  assessments, controls) via the FastAPI backend. Keep deterministic business logic (scoring,
  rating, state transitions) in the backend, not in a tool or a prompt.
- `rag/` — evidence ingestion (policies, procedures, audit reports, prior assessments), chunking,
  embeddings, and retrieval. Start with PostgreSQL + pgvector when this work begins — no new
  infrastructure needed today since it isn't built yet.

## Build order (first AI feature)

"Assist Me With This Assessment" — the assessor answers a question and supplies evidence; the AI
suggests a rating, explains why, and cites supporting evidence. The user must explicitly accept
the recommendation before it's saved (human-in-the-loop, not autonomous).

Requires: an OpenAI API key, the `openai-agents` package, and — once RAG is in scope — a
Postgres+pgvector database (the app currently runs on SQLite; that migration should happen
alongside this work, not before it).
