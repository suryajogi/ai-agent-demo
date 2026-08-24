# Aligned Product Backlog

**Cascading Risks: Asset Failures Impacting Upstream Components**

* Identify risks related to asset failures and their potential impact on upstream components
* Define risk rating and scoring criteria based on asset failure likelihood and impact
* Develop a workflow to escalate risk assessments to relevant stakeholders for mitigation and control

**Control Self-Assessments: Automated Validation Criteria Metrics**

* Create a risk assessment methodology that includes configurable questions, answer choices, and scoring rules
* Develop automated validation criteria to ensure risk assessments are comprehensive and accurate
* Integrate risk assessment methodology with the risk assessment workflow for seamless tracking and reporting

**Quantified Residual Risk Formula**

* Define a formula to calculate residual risk based on inherent risk and control effectiveness
* Develop a data model to track and store risk assessment results, including likelihood, impact, and residual risk scores
* Integrate the residual risk formula with the risk assessment workflow to provide real-time risk scores and recommendations

**Initial Requirements**

* AI-Powered Risk Management Platform
* Practical 12-week learning and build roadmap for a ServiceNow developer
* Goal: build a ServiceNow-inspired Risk Management application outside ServiceNow while learning modern AI application and agent development

**Target Architecture**

* Frontend: Next.js + React
* Backend: Python + FastAPI
* Database: PostgreSQL
* Vector search: PostgreSQL + pgvector initially
* AI: OpenAI API
* Agent framework: OpenAI Agents SDK for Python
* Authentication: start simple; later use Microsoft Entra ID/Auth0 or another enterprise identity provider
* Deployment: local development first; cloud deployment later

**Data Model**

* Users
* Roles
* Risks
* Risk Tasks
* Risk Assessment Methodologies
* Risk Assessment Questions
* Risk Assessment Options
* Risk Assessments
* Risk Assessment Responses
* Risk Controls
* Risk Mitigations
* Audit Logs

**Risk UI**

* Risk List:
	+ Risk ID, description/title, owner, rating, and state
	+ Search/filter
	+ Create Risk button
* Risk Details with tabs for:
	+ Details
	+ Tasks
	+ Assessments
	+ Controls
* Create Risk should include:
	+ Risk name and description
	+ Category
	+ Risk owner
	+ Risk source
	+ Likelihood
	+ Impact
	+ Automatically calculated inherent risk

**Risk Tasks**

* Each risk can have multiple tasks:
	+ Task name and description
	+ Assignee
	+ Due date
	+ Priority
	+ State
	+ Completion/history

**Risk Assessment Methodology**

* Make the methodology configurable instead of hard-coding assessment questions
* A methodology can contain:
	+ Name and description
	+ Assessment type/context
	+ Scoring method
	+ Questions
	+ Question type
	+ Sequence
	+ Required flag
	+ Weight
	+ Answer options and scores
	+ Scoring rules

**Risk Assessment Creation**

* User should be able to create an assessment by selecting:
	+ Risk
	+ Methodology
	+ Assignee
	+ Due date
* Creating the assessment should instantiate the methodology's questions as assessment response records

**Assignee Assessment Workspace**

* One question at a time or a structured questionnaire
* Answer choices
* Evidence/comments
* Save Draft
* Submit Assessment
* After submission, show deterministic results such as likelihood, impact, inherent risk, control effectiveness, and residual risk

**AI Features**

* Add AI only after the non-AI application works
* First AI feature to build: "Assist Me With This Assessment"
* The assessor answers a question and supplies evidence. The AI can suggest a rating, explain why, identify supporting evidence, and ask for missing evidence. The user must explicitly accept the recommendation.

**RAG Architecture**

* Use RAG for organizational evidence rather than putting every document into every prompt
* Upload policies, procedures, audit reports, and previous assessments
* Extract and chunk text
* Create embeddings
* Store embeddings and metadata
* Retrieve relevant passages for the user's question
* Give retrieved evidence to the LLM
* Return an answer with supporting source references

**Agent Architecture**

* Risk Manager Agent: get/search/analyze risks, tasks, controls, and assessments
* Assessment Agent: inspect methodology, questions, and responses
* Evidence Agent: search policies, reports, and previous assessments
* Compliance Agent: analyze requirements and evidence
* Manager can delegate to specialist agents. Use guardrails and human approval for consequential actions.

**Tools Needed**

* VS Code or another IDE
* Git
* GitHub
* Python 3.10+
* Node.js / npm
* Next.js / React
* FastAPI
* PostgreSQL
* pgvector
* Docker Desktop
* Postman or Bruno for API testing
* OpenAI API account/API key
* OpenAI Agents SDK for Python
* Optional later: Microsoft Entra ID, cloud object storage, CI/CD, monitoring, and an external vector database.

**GitHub Libraries and Repositories**

* Start with the official OpenAI Agents SDK repositories and examples:
	+ OpenAI Agents SDK for Python: https://github.com/openai/openai-agents-python
	+ OpenAI Agents SDK for TypeScript: https://github.com/openai/openai-agents-js
	+ OpenAI Agents SDK documentation: https://openai.github.io/openai-agents-python/

**Do You Need a Server?**

* No server is required to start.
* Development: run Next.js, FastAPI, and PostgreSQL locally on your laptop.
* AI model: your application calls the OpenAI API over the internet; you do not need a GPU or local LLM server.
* Database: PostgreSQL can run locally in Docker.
* Production: you will need cloud hosting or a server/service for the web app, backend, and database.

**Suggested Deployment Evolution**

* Stage 1: Laptop + Docker + local PostgreSQL
* Stage 2: GitHub + cloud frontend/backend/database
* Stage 3: Managed authentication, backups, monitoring, and secrets management
* Stage 4: Enterprise deployment with private networking, SSO, audit logging, and stronger security controls

**Estimated Cost**

* These are planning estimates, not vendor quotes.
* The cost depends heavily on traffic, model usage, document volume, and hosting choices.
* For a personal learning project, I would budget about $20-$50/month initially. You can keep most infrastructure local and pay primarily for API usage.

**12-Week Roadmap**

* Week 1-2: Build Risk Management data model and REST API
* Week 3-4: Build Risk Management UI
* Week 5-6: Integrate AI features and RAG architecture
* Week 7-8: Develop Agent architecture and workflows
* Week 9-10: Integrate authentication and authorization
* Week 11-12: Test and refine application

**Recommended GitHub Project Structure**

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

**Key AI Engineering Principles for This Project**

* Keep deterministic business rules in application code, not in the LLM.
* Give agents narrow, well-defined tools.
* Require human approval for high-impact actions.
* Use RAG for enterprise evidence and source-backed answers.
* Log and evaluate agent behavior.
* Design authorization before exposing tools that can modify data.
* Start with one agent; add multi-agent orchestration only when it solves a real problem.
* Do not fine-tune or train a model for the first version.

**What Success Looks Like**

* At the end of the project, you should have a working Risk Management application that demonstrates both traditional enterprise software engineering and modern AI engineering:
	+ Risk management CRUD and workflows
	+ Configurable assessment methodologies
	+ Dynamic risk scoring
	+ RAG over risk evidence
	+ AI-assisted assessments
	+ Tool-enabled AI agents
	+ Multi-agent risk analysis
	+ Human approval and guardrails
	+ Authentication/authorization
	+ Audit trail
	+ Cloud deployment

This is a strong portfolio project for positioning yourself as a ServiceNow + AI Agent developer because you can explain both the enterprise domain and the underlying AI architecture.