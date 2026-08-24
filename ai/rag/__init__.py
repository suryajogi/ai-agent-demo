"""RAG pipeline for organizational evidence (not yet implemented).

PRODUCT_BACKLOG.md section 12: upload policies/procedures/audit reports/prior
assessments -> extract & chunk text -> create embeddings -> store embeddings +
metadata -> retrieve relevant passages -> give retrieved evidence to the LLM ->
return an answer with source references.

Start with PostgreSQL + pgvector when this work begins (the app currently runs on
SQLite; that migration should land alongside this work, not before it).
"""
