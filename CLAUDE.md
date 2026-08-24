## ServiceNow GRC Database Schema Blueprint

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
