"""Function-calling tools for the agents in ai/agents/ (not yet implemented).

Each tool should be a narrow, well-defined function that calls the FastAPI backend
(http://localhost:8000/api/v1/...) rather than touching the database directly, so
authorization and validation stay in one place. Deterministic scoring/business
rules stay in backend/main.py — never delegate them to the LLM.
"""
