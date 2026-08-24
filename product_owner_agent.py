import os
from datetime import datetime

class ProductOwnerAgent:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.backlog_path = os.path.join(self.root_dir, "PRODUCT_BACKLOG.md")
        
    def review_current_build(self):
        """Inspects codebase layout folders to see what has been built vs what is missing."""
        has_backend = os.path.exists(os.path.join(self.root_dir, "backend"))
        has_frontend = os.path.exists(os.path.join(self.root_dir, "frontend"))
        
        # Look for advanced ServiceNow GRC components
        has_matrix = False
        if has_frontend:
            for root, _, files in os.walk(os.path.join(self.root_dir, "frontend")):
                for f in files:
                    if "matrix" in f.lower() or "grid" in f.lower():
                        has_matrix = True
                        break
        return {"backend": has_backend, "frontend": has_frontend, "matrix_visualizer": has_matrix}

    def formulate_new_requirements(self):
        print("📋 Product Owner Agent: Reviewing repository build state to prioritize backlog...")
        state = self.review_current_build()
        
        # Define advanced feature requirements to transform the project into a "perfect" system
        backlog_content = f"""# 📋 ServiceNow GRC Replication: Product Backlog
*Compiled by the AI Product Owner Agent on {datetime.now().strftime('%Y-%m-%d')}*

## 🎯 Vision Statement
Transform the lightweight local repository into a production-grade enterprise replication of ServiceNow GRC: Risk Management, ensuring complete auditable isolation between policy registries, mitigating controls, and data telemetry.

---

## 🛠️ Phase 2 Expansion Requirements (Assigned to Claude Code)

### 📈 Requirement 1: Interactive Heatmap Matrix Grid (High Priority)
- **Description:** Implement a color-coded 5x5 structural visual matrix mapping Likelihood (1-5 axes) vs Impact (1-5 axes) on the main dashboard view.
- **Behavior:** Clicking a specific coordinate cell (e.g., cell [4,3] High Likelihood, Medium Impact) must dynamically filter and isolate the data table below to show only the specific risks matching those scoring weights.

### 🔐 Requirement 2: Audit Trait History Logging Pipeline (Medium Priority)
- **Description:** Implement automatic mutation tracking for the `risks` database table.
- **Behavior:** When an assessor updates a risk state from `Assess` to `Respond`, a backend hook must automatically log a timestamped tracking row into a new `audit_logs` model tracking who changed the value, when, and the historic state delta.

### 🤖 Requirement 3: Automated Control Testing Simulator (Medium Priority)
- **Description:** Build an event simulator endpoint (`/api/v1/simulation/trigger-test`).
- **Behavior:** Running this simulation randomly triggers a "Fail" or "Pass" metric against deployed mitigation controls. If a control status flips to "Fail", the engine must automatically create a new High Priority record in the `issues` database table linked to that asset.
"""
        with open(self.backlog_path, "w") as f:
            f.write(backlog_content)
        
        print(f"🎯 Requirements generated successfully! Updated: {self.backlog_path}")
        
        # Display the handoff instruction command directly to the terminal screen
        print("\n" + "="*80)
        print("🤖 PRODUCT OWNER HANDOFF STATEMENT FOR CLAUDE CODE:")
        print("="*80)
        print("Copy and paste the exact command instruction prompt below into your `claude` terminal agent:")
        print("\n\"Please read @PRODUCT_BACKLOG.md. Implement Requirement 1 (Interactive Heatmap Matrix Grid) on the frontend page and add the Requirement 3 Simulation endpoints into the FastAPI backend file layout.\"")
        print("="*80 + "\n")

if __name__ == "__main__":
    agent = ProductOwnerAgent(os.path.expanduser("~/Desktop/ai-agent-demo"))
    agent.formulate_new_requirements()
