"""Risk Manager Agent (not yet implemented).

Top-level orchestrator described in PRODUCT_BACKLOG.md section 13. Delegates to the
specialist agents below based on the user's request, using the OpenAI Agents SDK's
handoff mechanism. Requires human approval before any consequential (write) action.

Specialists to delegate to:
- risk_agent: get/search/analyze risks, tasks, controls, assessments
- assessment_agent: inspect methodology, questions, responses
- evidence_agent: search policies, reports, previous assessments (RAG)
"""
