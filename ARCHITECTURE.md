# 📑 ServiceNow GRC Replication Architecture Manual
*Generated automatically by Documentation Agent on 2026-08-25*

---

## 🏗️ 1. Global System Architecture
This project replicates the data relationships and form structures of the **ServiceNow GRC: Risk Management** module outside of the ServiceNow platform ecosystem. It splits the core responsibilities cleanly into a headless API engine layer, a single-page web dashboard application workspace, and a handful of standalone role-playing automation scripts that exercise the live API.

### Core Repository Directory Topology
```text
📁 ai-agent-demo/
    ├── 📄 agentic_workflow.py
    ├── 📄 product_owner_agent.py
    ├── 📄 documentation_agent.py
    ├── 📄 end_user_agent.py
    ├── 📄 PRODUCT_BACKLOG.md
    ├── 📄 CLAUDE.md
    ├── 📄 AGENTS.md
    ├── 📄 ARCHITECTURE.md
    ├── 📄 README.md
    ├── 📄 assessor_agent.py
    ├── 📄 summary_email_agent.py
    ├── 📄 PRODUCT_BACKLOG_CANDIDATES.csv
    ├── 📄 requirements.docx
    ├── 📁 backend/
        ├── 📄 scoring.py
        ├── 📄 main.py
        ├── 📄 schemas.py
        ├── 📄 init_db.py
        ├── 📄 control_testing.py
        ├── 📄 models.py
        ├── 📄 database.py
        ├── 📄 requirements.txt
        ├── 📄 auth.py
        ├── 📄 reporting_agent.py
    ├── 📁 tests/
        ├── 📄 README.md
    ├── 📁 .github/
        ├── 📁 workflows/
            ├── 📄 doc-update.yml
    ├── 📁 frontend/
        ├── 📄 eslint.config.mjs
        ├── 📄 CLAUDE.md
        ├── 📄 AGENTS.md
        ├── 📄 package.json
        ├── 📄 package-lock.json
        ├── 📄 README.md
        ├── 📄 tsconfig.json
        ├── 📄 postcss.config.mjs
        ├── 📄 next.config.ts
        ├── 📁 app/
            ├── 📄 MetricBanner.tsx
            ├── 📄 globals.css
            ├── 📄 layout.tsx
            ├── 📄 page.tsx
            ├── 📄 favicon.ico
            ├── 📁 workspace/
                ├── 📄 ControlForm.tsx
                ├── 📄 EvidenceList.tsx
                ├── 📄 RiskHeatmap.tsx
                ├── 📄 page.tsx
                ├── 📄 AssessmentLauncherForm.tsx
                ├── 📄 DepartmentForm.tsx
                ├── 📄 NotificationBell.tsx
                ├── 📄 EntityForm.tsx
                ├── 📄 ui.tsx
                ├── 📄 RiskForm.tsx
                ├── 📄 ControlTestHistory.tsx
                ├── 📄 IssueForm.tsx
            ├── 📁 assessor/
                ├── 📄 page.tsx
            ├── 📁 login/
                ├── 📄 page.tsx
        ├── 📁 public/
            ├── 📄 next.svg
            ├── 📄 file.svg
            ├── 📄 window.svg
            ├── 📄 globe.svg
            ├── 📄 vercel.svg
        ├── 📁 lib/
            ├── 📄 api.ts
    ├── 📁 ai/
        ├── 📄 README.md
        ├── 📁 agents/
            ├── 📄 __init__.py
            ├── 📄 evidence_agent.py
            ├── 📄 risk_agent.py
            ├── 📄 manager_agent.py
            ├── 📄 assessment_agent.py
        ├── 📁 tools/
            ├── 📄 __init__.py
        ├── 📁 rag/
            ├── 📄 __init__.py
```

---

## 💻 2. Tech Stack Blueprint
- **Backend API Layer:** Python 3.12, FastAPI, Uvicorn ASGI server, SQLAlchemy ORM.
- **Auth:** JWT bearer tokens (`python-jose`) + bcrypt password hashing (`passlib`) — writes require a token, GET stays open for the read-only dashboard experience.
- **Relational Storage:** SQLite, local file `backend/grc.db` (created/reset via `init_db.py`; no migration tool — schema changes are applied by editing `models.py` and reseeding).
- **Other backend deps:** `python-multipart` (file uploads), `httpx` (outbound control-test connector calls), `fpdf2` (PDF report generation).
- **Frontend Dashboard:** React 19, Next.js 16 (App Router), Tailwind CSS v4, TypeScript.
- **Package Management:** `uv` (Python backend), `npm` (frontend).

---

## 🗄️ 3. Backend Architecture (`/backend`)
- **`models.py`**: ~25 tables spanning identity (`roles`, `users`), org structure (`departments`, `entities` — with vendor lifecycle fields), risk governance (`risk_scopes`, `risk_methodologies`, `risk_frameworks`, `risk_statements`, `risks`), execution (`risk_assessments`, `risk_tasks`, `projects`), compliance (`controls`, `issues` — with CAPA fields, `risk_mitigations`, `control_framework_map`, `risk_appetite_thresholds`), the assessment engine (`assessment_templates`, `assessment_questions`, `assessment_options`, `assessment_responses`), and supporting tables (`evidence_attachments`, `control_test_results`, `notifications`, `risk_score_history`, `audit_logs`).
- **`main.py`**: a generic CRUD router factory (`build_crud_router`) drives every resource's list/get/create/update/delete endpoints, extended with role gates, free-text search, department-scoped multi-tenancy, and per-resource hooks (a segregation-of-duties gate on risk acceptance, a CAPA-closure gate on issues, auto-instantiating assessment responses on creation). Custom endpoints layer on top for auth, evidence upload/download, CSV bulk import/export, PDF/board reporting, notifications, recurring-assessment generation, and pluggable control testing.
- **`auth.py`**: login/token issuance, password hashing, and the `require_user`/`require_roles` FastAPI dependencies used across the router.
- **`scoring.py`** / **`control_testing.py`**: configurable risk-scoring bands per methodology, and pluggable control-test connectors (a real HTTP health-check connector, falling back to the original simulated Pass/Fail for unconfigured controls).
- **`init_db.py`**: seeds departments, entities, the full risk/control/issue/assessment register, appetite thresholds, and demo user accounts (password `changeme123` for every seeded `user.NNN`).
- **`reporting_agent.py`**: standalone executive-summary printout, run manually from `backend/`.

---

## 🎨 4. Frontend Workspace UI (`/frontend`)
- **`/login`**: JWT sign-in; the dashboard itself stays browsable read-only without an account.
- **Interface A — `/workspace`**: six tabs (Risks, Controls, Issues, Departments, Entities, Assessments), each backed by a shared `DataTable`/`DetailModal`/`Card` set of primitives (`app/workspace/ui.tsx`) and a per-resource `*Form` component. Adds evidence attachment upload, appetite-breach badges, CSV import/export, PDF export, an in-app notifications widget, and control test-history/connector configuration on top of standard CRUD.
- **Interface B — `/assessor`**: a self-declared-identity questionnaire portal that submits scored answers through the same backend the CLI `assessor_agent.py` script drives.
- **Live Metric Banner** (home page): fetches `/api/v1/dashboard/stats` for a real-time risk/control/issue snapshot.

---

## 🔗 5. Integration Framework & Pipelines
- **Frontend ↔ Backend:** Next.js talks to FastAPI over CORS-enabled `fetch`; the backend runs on port **8050** (see `README.md` / `frontend/.env.local`), the frontend on 3000.
- **Reporting:** `/api/v1/reports/risk-summary` (JSON), `/api/v1/reports/risk-summary/pdf` (board-ready PDF), `/api/v1/reports/risk-summary/history` (trend snapshots).
- **CI:** `.github/workflows/doc-update.yml` re-runs this Documentation Agent on every push to `main` and commits `ARCHITECTURE.md` back if it changed.

---

## 🤖 6. Automation Scripts (repo root)
A consistent convention — a small class taking `root_dir`, one clearly-named method, emoji-prefixed status prints, `if __name__ == "__main__"` entry point:
- **`documentation_agent.py`**: this script — regenerates this file.
- **`product_owner_agent.py`**: reads `requirements.docx` + the live schema and appends new candidate requirements to `PRODUCT_BACKLOG_CANDIDATES.csv` via a local Ollama model, without ever overwriting existing rows or a reviewer's decisions.
- **`end_user_agent.py`** / **`assessor_agent.py`**: log into the *live* API as seeded demo users and create records / submit assessments over real HTTP, exercising real auth and RBAC.
- **`summary_email_agent.py`**: pulls the live risk summary + PDF and drafts (does not send, by default) an executive email into `reports/`.
- **`agentic_workflow.py`**: an experimental full-autonomy pipeline that regenerates `backend/main.py` via a local model and auto-commits/pushes to `main` with no review gate — higher risk than the scripts above; not a template to copy for new automation.
