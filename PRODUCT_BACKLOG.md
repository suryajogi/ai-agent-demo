# 📋 Aligned Product Backlog & Target Vision
*Synthesized by Product Owner Agent on 2026-08-24*

---

## 📄 Ingested Document Requirements (From requirements.docx)

### AI-Powered Risk Management Platform
A practical 12-week learning and build roadmap for a ServiceNow developer
Goal: build a ServiceNow-inspired Risk Management application outside ServiceNow while learning modern AI application and agent development.

### 1. Why this is a good AI project for a ServiceNow developer
Your existing ServiceNow and JavaScript experience maps directly to modern AI application concepts. The objective is not to become an ML researcher. It is to learn how to build enterprise applications that use LLMs, RAG, tools, agents, workflows, authorization and human approval.

### 2. The application to build
Build a mini enterprise Risk Management platform with these modules:

### Dashboard
Risks: create, view, update, ownership, rating, state and history

### Risk Tasks: create, assign, prioritize, track and complete
Risk Assessment Methodologies: configurable methodologies, questions, answer choices, weights and scoring rules
Risk Assessments: create assessments against risks, assign assessors and track state
Assignee Assessment Workspace: a focused UI where an assignee answers questions, adds evidence/comments, saves drafts and submits
Assessment Results: deterministic scoring, inherent/residual risk and recommendations
AI Risk Assistant: AI-assisted descriptions, summaries, evidence analysis and recommendations

### 3. Target architecture

### A simple production-oriented architecture is recommended:

### Frontend: Next.js + React

### Backend: Python + FastAPI

### Database: PostgreSQL

### Vector search: PostgreSQL + pgvector initially

### AI: OpenAI API

### Agent framework: OpenAI Agents SDK for Python
Authentication: start simple; later use Microsoft Entra ID/Auth0 or another enterprise identity provider

### Deployment: local development first; cloud deployment later
The official OpenAI Agents SDK supports agents, tools/function calling, handoffs, guardrails, sessions, human-in-the-loop and tracing. It is Python-first and can manage multi-step agent workflows. For a JavaScript/TypeScript-heavy developer, there is also an official TypeScript SDK.

### 4. Data model

### Start with these core entities:

### users

### roles

### risks

### risk_tasks

### risk_assessment_methodologies

### risk_assessment_questions

### risk_assessment_options

### risk_assessments

### risk_assessment_responses

### risk_controls

### risk_mitigations

### audit_logs

### Relationship:
Risk → Tasks, Assessments, Controls. Assessment → Methodology → Questions → Responses.

### 5. Risk UI

### Risk List:

### Risk ID, description/title, owner, rating and state

### Search/filter

### Create Risk button
Risk details with tabs for Details, Tasks, Assessments and Controls

### Create Risk should include:

### Risk name and description

### Category

### Risk owner

### Risk source

### Likelihood

### Impact

### Automatically calculated inherent risk
Keep scoring deterministic. For example, likelihood 4 × impact 5 = score 20, then map the score to a configured rating. Do not ask the LLM to perform deterministic business calculations.

### 6. Risk Tasks

### Each risk can have multiple tasks:

### Task name and description

### Assignee

### Due date

### Priority

### State

### Completion/history

### 7. Risk Assessment Methodology
Make the methodology configurable instead of hard-coding assessment questions. A methodology can contain:

### Name and description

### Assessment type/context

### Scoring method

### Questions

### Question type

### Sequence

### Required flag

### Weight

### Answer options and scores

### Scoring rules
This is the foundation for a dynamic assessment engine and closely matches the enterprise configuration mindset you already know from ServiceNow.

### 8. Risk Assessment creation

### A user should be able to create an assessment by selecting:

### Risk

### Methodology

### Assignee

### Due date
Creating the assessment should instantiate the methodology's questions as assessment response records.

### 9. Assignee Assessment Workspace
This is one of the most important screens.

### My Risk Assessments list

### Assigned / In Progress / Completed states

### Assessment details

### One question at a time or a structured questionnaire

### Answer choices

### Evidence/comments

### Save Draft

### Submit Assessment
After submission, show deterministic results such as likelihood, impact, inherent risk, control effectiveness and residual risk.

### 10. AI features
Add AI only after the non-AI application works.

### 11. First AI feature to build
Build “Assist Me With This Assessment” first.
The assessor answers a question and supplies evidence. The AI can suggest a rating, explain why, identify supporting evidence and ask for missing evidence. The user must explicitly accept the recommendation.
This single feature teaches prompts, structured outputs, tool calling, RAG, citations, human-in-the-loop and UI/API integration.

### 12. RAG architecture
Use RAG for organizational evidence rather than putting every document into every prompt:
Upload policies, procedures, audit reports and previous assessments

### Extract and chunk text

### Create embeddings

### Store embeddings and metadata

### Retrieve relevant passages for the user's question

### Give retrieved evidence to the LLM

### Return an answer with supporting source references
Start with PostgreSQL + pgvector to avoid unnecessary infrastructure.

### 13. Agent architecture

### A useful eventual design is:

### Risk Manager Agent
Risk Agent: get/search/analyze risks, tasks, controls and assessments
Assessment Agent: inspect methodology, questions and responses
Evidence Agent: search policies, reports and previous assessments

### Compliance Agent: analyze requirements and evidence
The manager can delegate to specialist agents. Use guardrails and human approval for consequential actions.

### 14. Tools needed

### Recommended development stack:

### VS Code or another IDE

### Git

### GitHub

### Python 3.10+

### Node.js / npm

### Next.js / React

### FastAPI

### PostgreSQL

### pgvector

### Docker Desktop

### Postman or Bruno for API testing

### OpenAI API account/API key

### OpenAI Agents SDK for Python
Optional later: Microsoft Entra ID, cloud object storage, CI/CD, monitoring and an external vector database.

### 15. GitHub libraries and repositories
Start with the official OpenAI Agents SDK repositories and examples:
OpenAI Agents SDK for Python: https://github.com/openai/openai-agents-python
OpenAI Agents SDK for TypeScript: https://github.com/openai/openai-agents-js
OpenAI Agents SDK documentation: https://openai.github.io/openai-agents-python/
The Python SDK is the recommended starting point for this roadmap because it is Python-first and provides tools, handoffs, guardrails, sessions, human-in-the-loop and tracing. If you want to remain mostly in JavaScript/TypeScript, use the official JS SDK.
Do not clone a large enterprise application and try to understand everything. Start from the SDK quickstart, then examples, and progressively replace the example tools with your Risk Management tools.

### 16. Do you need a server?
No server is required to start.
Development: run Next.js, FastAPI and PostgreSQL locally on your laptop.
AI model: your application calls the OpenAI API over the internet; you do not need a GPU or local LLM server.
Database: PostgreSQL can run locally in Docker.
Production: you will need cloud hosting or a server/service for the web app, backend and database.
For learning and the first prototype, a normal laptop is sufficient. You do not need to buy a physical server.

### 17. Suggested deployment evolution

### Stage 1: Laptop + Docker + local PostgreSQL

### Stage 2: GitHub + cloud frontend/backend/database
Stage 3: Managed authentication, backups, monitoring and secrets management
Stage 4: Enterprise deployment with private networking, SSO, audit logging and stronger security controls

### 18. Estimated cost
These are planning estimates, not vendor quotes. The cost depends heavily on traffic, model usage, document volume and hosting choices.
For a personal learning project, I would budget about $20–$50/month initially. You can keep most infrastructure local and pay primarily for API usage.
As an example of current model economics, OpenAI's published GPT-5 pricing lists $1.25 per 1M input tokens and $10 per 1M output tokens; GPT-5 mini is listed at $0.25 per 1M input and $2 per 1M output. Actual project cost depends on model choice and usage.

### 19. 12-week roadmap

### 20. Recommended GitHub project structure
risk-management-ai/
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   ├── risks/
│   │   ├── assessments/
│   │   ├── methodologies/
│   │   └── my-assessments/
│   ├── components/
│   └── services/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── database/
├── ai/
│   ├── agents/
│   │   ├── risk_agent.py
│   │   ├── assessment_agent.py
│   │   ├── evidence_agent.py
│   │   └── manager_agent.py
│   ├── tools/
│   └── rag/
├── tests/
├── docs/
└── README.md

### 21. Key AI engineering principles for this project
Keep deterministic business rules in application code, not in the LLM.
Give agents narrow, well-defined tools.
Require human approval for high-impact actions.
Use RAG for enterprise evidence and source-backed answers.
Log and evaluate agent behavior.
Design authorization before exposing tools that can modify data.
Start with one agent; add multi-agent orchestration only when it solves a real problem.
Do not fine-tune or train a model for the first version.

### 22. What success looks like
At the end of the project you should have a working Risk Management application that demonstrates both traditional enterprise software engineering and modern AI engineering:

### Risk management CRUD and workflows

### Configurable assessment methodologies

### Dynamic assessment engine

### Assignee assessment workspace

### Deterministic risk scoring

### RAG over risk evidence

### AI-assisted assessments

### Tool-enabled AI agents

### Multi-agent risk analysis

### Human approval and guardrails

### Authentication/authorization

### Audit trail

### Cloud deployment
This is a strong portfolio project for positioning yourself as a ServiceNow + AI Agent developer because you can explain both the enterprise domain and the underlying AI architecture.

### 23. Recommended starting point
Do not spend the first month only watching AI courses. Start by building the Risk Management data model and REST API. Then build the UI. Once the normal application works, add AI one feature at a time. This keeps the learning concrete and lets you compare every new concept to something you already know from ServiceNow.

### Sources and current references
OpenAI Agents SDK Python repository and documentation: https://github.com/openai/openai-agents-python and https://openai.github.io/openai-agents-python/
OpenAI Agents SDK TypeScript repository and documentation: https://github.com/openai/openai-agents-js
OpenAI model/pricing reference used for the planning estimate: https://openai.com/gpt-5/ and https://developers.openai.com/api/docs/models/gpt-5

---

## 🏗️ Architectural Compliance Analysis
The Product Owner has checked your current local code footprint relative to the custom Word document goals:
- **Backend Architecture Integration:** 🟢 Existing FastAPI schemas detected.
- **Frontend Presentation Layer:** 🟢 Next.js UI component space active.

---

## 🛠️ Refined Directive Backlog for Engineering Agent (Claude Code)
Based directly on your Word specifications, build the following updates:
1. Cross-reference the database tables to match any specialized data tracking columns specified in the Word document.
2. Refine form validation boundaries on the frontend components to handle data fields accurately as outlined above.
3. Keep the 50 mocked dataset entries per table running flawlessly to enable proper application evaluation.
