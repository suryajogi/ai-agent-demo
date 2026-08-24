# 📑 ServiceNow GRC Replication Architecture Manual
*Generated automatically by Documentation Agent on 2026-08-24*

---

## 🏗️ 1. Global System Architecture
This project replicates the data relationships and form structures of the **ServiceNow GRC: Risk Management** module outside of the ServiceNow platform ecosystem. It splits the core responsibilities cleanly into a headless API engine layer and a single-page web dashboard application workspace.

### Core Repository Directory Topology
```text
📁 ai-agent-demo/
    ├── 📄 README.md
    ├── 📄 documentation_agent.py
    ├── 📄 AGENTS.md
    ├── 📄 CLAUDE.md
    ├── 📁 frontend/
        ├── 📄 postcss.config.mjs
        ├── 📄 tsconfig.tsbuildinfo
        ├── 📄 next-env.d.ts
        ├── 📄 README.md
        ├── 📄 package-lock.json
        ├── 📄 package.json
        ├── 📄 tsconfig.json
        ├── 📄 AGENTS.md
        ├── 📄 eslint.config.mjs
        ├── 📄 CLAUDE.md
        ├── 📄 next.config.ts
        ├── 📁 app/
            ├── 📄 favicon.ico
            ├── 📄 MetricBanner.tsx
            ├── 📄 layout.tsx
            ├── 📄 page.tsx
            ├── 📄 globals.css
            ├── 📁 workspace/
                ├── 📄 ControlForm.tsx
                ├── 📄 DepartmentForm.tsx
                ├── 📄 AssessmentLauncherForm.tsx
                ├── 📄 IssueForm.tsx
                ├── 📄 page.tsx
                ├── 📄 RiskForm.tsx
                ├── 📄 ui.tsx
            ├── 📁 assessor/
                ├── 📄 page.tsx
        ├── 📁 public/
            ├── 📄 file.svg
            ├── 📄 vercel.svg
            ├── 📄 next.svg
            ├── 📄 globe.svg
            ├── 📄 window.svg
        ├── 📁 lib/
            ├── 📄 api.ts
    ├── 📁 backend/
        ├── 📄 models.py
        ├── 📄 requirements.txt
        ├── 📄 database.py
        ├── 📄 schemas.py
        ├── 📄 reporting_agent.py
        ├── 📄 main.py
        ├── 📄 init_db.py
```

---

## 💻 2. Tech Stack Blueprint
- **Backend API Layer:** Python 3.12, FastAPI framework, Uvicorn ASGI production server, SQLAlchemy ORM toolkit.
- **Relational Storage:** SQLite database file local instance (`grc_risk.db`).
- **Frontend Dashboard:** React Framework, Next.js rendering engine architecture, Tailwind CSS utilities framework.
- **Package Management:** `uv` environment system (Python backend), `fnm` Node runtime supervisor (Frontend).

---

## 🗄️ 3. Backend Architecture (`/backend`)
The data layer replicates the underlying schema properties of ServiceNow GRC records:
- **`models.py`**: Declares structured entity mapping fields for Organizational tables (`departments`, `entities`), Governance policies (`risk_scopes`, `risk_methodologies`), Risk Registries (`risk_frameworks`, `risk_statements`, `risks`), Operations (`risk_assessments`, `risk_tasks`), and Compliance extensions (`controls`, `issues`).
- **`init_db.py`**: Mass-seeding automation pipeline file that structures relational constraints and feeds exactly **50 comprehensive sample rows** to each table to fulfill system demo stress-testing metrics.
- **`main.py`**: Exposes complete HTTP CRUD (`GET`, `POST`, `PUT`, `DELETE`) API route paths, alongside optimized visual statistic aggregate paths (`/api/v1/dashboard/stats`).

---

## 🎨 4. Frontend Workspace UI (`/frontend`)
The presentation tier leverages modular rendering templates configured to isolate administrative dashboards from user-facing components:
- **Interface A (GRC Management Hub):** Houses inputs and entry fields allowing risk officers to author new risks, track issue items, and update department boundaries.
- **Interface B (Assessor Portal Workflow):** A streamlined questionnaire panel featuring a 1-5 scalar point layout that pushes active responses directly to the calculated database metrics engine.
- **Live Metric Counter Banner:** A dynamic fetching utility that eliminates standard text strings to highlight real-time numbers of profiled risks, failed controls, and pending audit reviews.

---

## 🔗 5. Integration Framework & Pipelines
- **Internal Integration Bridge:** Communication between Next.js and FastAPI uses standard asynchronous HTTP `fetch` connections addressing cross-origin parameters (`CORS`).
- **Database Handshake Bridge:** Models leverage external foreign key anchors (`FK`) to map operational controls back to primary asset profiles and risk statement indices automatically.
- **Reporting Agent Endpoint Link:** A unified data export node `/api/v1/reports/risk-summary` is established to translate running rows into diagnostic executive overview briefs.
