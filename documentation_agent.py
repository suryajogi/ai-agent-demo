import os
from datetime import datetime

class DocumentationAgent:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.doc_file_path = os.path.join(self.root_dir, "ARCHITECTURE.md")
        
    def generate_directory_tree(self, startpath, exclude_dirs=None):
        """Generates a scannable text directory map of the project structure."""
        if exclude_dirs is None:
            exclude_dirs = ['.git', '.venv', '__pycache__', 'node_modules', '.next', '.claude', '.cursor']
        
        tree_lines = []
        for root, dirs, files in os.walk(startpath):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            folder_name = os.path.basename(root)
            if folder_name == os.path.basename(startpath):
                tree_lines.append(f"📁 {folder_name}/")
            else:
                tree_lines.append(f"{indent}├── 📁 {folder_name}/")
            
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if not f.startswith('.') and not f.endswith('.db'):
                    tree_lines.append(f"{sub_indent}├── 📄 {f}")
        return "\n".join(tree_lines)

    def write_architecture_manual(self):
        """Compiles codebase layouts into a unified architecture manual."""
        print("🤖 Documentation Agent: Analyzing workspace configurations...")
        
        # Capture current codebase structures
        full_tree = self.generate_directory_tree(self.root_dir)
        backend_exists = os.path.exists(os.path.join(self.root_dir, "backend"))
        frontend_exists = os.path.exists(os.path.join(self.root_dir, "frontend"))

        markdown_content = f"""# 📑 ServiceNow GRC Replication Architecture Manual
*Generated automatically by Documentation Agent on {datetime.now().strftime('%Y-%m-%d')}*

---

## 🏗️ 1. Global System Architecture
This project replicates the data relationships and form structures of the **ServiceNow GRC: Risk Management** module outside of the ServiceNow platform ecosystem. It splits the core responsibilities cleanly into a headless API engine layer and a single-page web dashboard application workspace.

### Core Repository Directory Topology
```text
{full_tree}
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
"""

        with open(self.doc_file_path, "w") as f:
            f.write(markdown_content)
        
        print(f"🎯 Documentation Agent complete! Created file: {self.doc_file_path}")

if __name__ == "__main__":
    # Target your local repository root
    agent = DocumentationAgent(os.path.expanduser("~/Desktop/ai-agent-demo"))
    agent.write_architecture_manual()
