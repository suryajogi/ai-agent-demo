## ServiceNow GRC Database Schema Blueprint

This is the authoritative schema for `backend/`. `PRODUCT_BACKLOG.md` describes a broader
target vision (AI Risk Assistant, RAG, agents, Postgres+pgvector) synthesized from an ingested
requirements doc — treat it as roadmap/direction, not as a schema replacement. Where the two
disagree on table/column names, this blueprint wins; the backlog's concepts (users/roles,
audit trail, configurable methodology, mitigations) have been folded into the sections below
rather than used to rename or replace what's already built. AI/RAG/agents work is intentionally
scaffolded only (`ai/`) and not implemented — build it after the core app, per the backlog's
own sequencing advice.

### 0. Identity
- **roles**: `id` (PK), `name`, `description`
- **users**: `id` (PK), `username`, `display_name`, `email`, `role_id` (FK), `active`

Note: this is a standalone identity table for future auth — existing `assigned_to`/`owner_id`/
`assessor_id` columns elsewhere remain free-text strings, not FKs to `users`, to avoid a wider
breaking migration.

### 1. Core Organizational Structure
- **departments**: `id` (PK), `name`, `manager_id`, `cost_center`
- **entities**: `id` (PK), `name`, `type` (e.g., Application, Facility, Vendor), `department_id` (FK), `owner_id`, `status` (Active, Inactive)

### 2. Risk Registry & Governance
- **risk_scopes**: `id` (PK), `name`, `description`, `version`
- **risk_methodologies**: `id` (PK), `name`, `assessment_type` (Qualitative, Quantitative, Hybrid), `scoring_logic`
- **risk_frameworks**: `id` (PK), `name`, `description`, `scope_id` (FK)
- **risk_statements**: `id` (PK), `name`, `description`, `category` (Strategic, Operational, Financial, Compliance), `framework_id` (FK)
- **risks**: `id` (PK), `name`, `description`, `statement_id` (FK), `entity_id` (FK), `assigned_to`, `state` (Draft, Assess, Respond, Review, Monitor), `inherent_likelihood`, `inherent_impact`, `residual_likelihood`, `residual_impact`

### 3. Execution & Operations
- **risk_assessments**: `id` (PK), `risk_id` (FK), `assessor_id`, `state` (Not Started, In Progress, Completed), `score`, `comments`
- **risk_tasks**: `id` (PK), `title`, `description`, `parent_risk_id` (FK), `assigned_to`, `due_date`, `state` (Open, Work in Progress, Closed Complete)
- **projects**: `id` (PK), `name`, `description`, `start_date`, `end_date`, `status`

### 4. Compliance & Issue Management (New)
- **controls**: `id` (PK), `name`, `description`, `status` (Draft, Attest, Review, Monitor, Fail), `entity_id` (FK), `risk_id` (FK, optional mitigation link)
- **issues**: `id` (PK), `title`, `description`, `source` (Risk Assessment, Control Failure, Manual), `priority` (Low, Medium, High, Critical), `state` (New, Analyze, Remediate, Closed), `assigned_to`
- **risk_mitigations**: `id` (PK), `risk_id` (FK), `control_id` (FK, optional), `description`, `status` (Planned, In Progress, Implemented, Verified), `owner`, `target_date`

### 5. Assessment Engine Structures (New)
- **assessment_templates**: `id` (PK), `name`, `description`, `metric_type` (Qualitative), `scoring_method`
- **assessment_questions**: `id` (PK), `template_id` (FK), `question_text`, `question_type` (Scale, MultipleChoice, YesNo), `sequence`, `required`, `weight`
- **assessment_options**: `id` (PK), `question_id` (FK), `label`, `score`, `sequence` — configurable answer choices per question. Seeded as a 1-5 Likert scale; `assessment_responses.selected_value` and the assessor UI still take a free 1-5 int rather than an `option_id` — options are metadata for a future config-driven UI, not yet wired into scoring.
- **assessment_responses**: `id` (PK), `assessment_id` (FK), `question_id` (FK), `selected_value` (1-5 scale), `justification`

### 6. Audit Trail (New)
- **audit_logs**: `id` (PK), `table_name`, `record_id`, `action` (created, updated, deleted), `field_name`, `old_value`, `new_value`, `changed_by`, `changed_at`
- Written automatically by the generic CRUD router in `backend/main.py` on every `PUT`/`DELETE` across all resources (one row per changed field on update; one row on delete). `changed_by` comes from an optional `X-User` request header, defaulting to `"system"` — there is no real auth yet. Read-only via `GET /api/v1/audit-logs` (filter by `table_name`, `record_id`).
