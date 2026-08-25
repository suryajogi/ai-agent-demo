import csv
import json
import os
import re
from datetime import date

import ollama

try:
    import docx
except ImportError:
    print("⚠️ python-docx missing. Run: uv pip install python-docx")

COLUMNS = [
    "id", "title", "category", "client_pain_point", "proposed_requirement",
    "why_it_matters", "related_gap", "priority", "effort", "status", "source", "date_added",
]


class ProductOwnerAgent:
    """
    Proposes NEW candidate requirements for PRODUCT_BACKLOG_CANDIDATES.csv,
    grounded in the original requirements.docx and the current backend schema.

    Safe by construction: every run is a structured merge, never a raw
    overwrite. A malformed or unparsable model response aborts the run and
    leaves the CSV untouched. Existing rows (and any `status` you've set by
    hand) are never modified — only new, non-duplicate rows are appended.
    """

    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.docx_path = os.path.join(self.root_dir, "requirements.docx")
        self.models_path = os.path.join(self.root_dir, "backend", "models.py")
        self.csv_path = os.path.join(self.root_dir, "PRODUCT_BACKLOG_CANDIDATES.csv")

    def extract_word_text(self):
        if not os.path.exists(self.docx_path):
            return ""
        try:
            doc = docx.Document(self.docx_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            print(f"⚠️ Failed to parse requirements.docx: {e}")
            return ""

    def summarize_schema(self):
        """Table names pulled straight from models.py so the prompt stays accurate
        as the schema evolves, without hand-maintaining a description here."""
        if not os.path.exists(self.models_path):
            return ""
        text = open(self.models_path).read()
        tables = re.findall(r'__tablename__\s*=\s*"([^"]+)"', text)
        return ", ".join(tables)

    def load_existing(self):
        if not os.path.exists(self.csv_path):
            return []
        with open(self.csv_path, newline="") as f:
            return list(csv.DictReader(f))

    def next_id(self, existing_rows):
        nums = [int(m.group(1)) for r in existing_rows if (m := re.match(r"NR-(\d+)", r.get("id", "")))]
        return (max(nums) + 1) if nums else 1

    def build_prompt(self, docx_text, schema_summary, existing_titles):
        avoid = "\n".join(f"- {t}" for t in sorted(existing_titles)) or "(none yet)"
        return f"""You are an elite enterprise Product Owner specializing in ServiceNow-style GRC platforms.

The current application's database tables are: {schema_summary}

The original project roadmap (for context only, do not restate it):
{docx_text[:4000]}

Requirements ALREADY proposed — do NOT repeat these titles or close variants:
{avoid}

Propose UP TO 5 NEW requirements that reflect how real enterprise GRC clients
(SOX, ISO 27001, vendor risk, internal audit programs) actually use these
platforms, and that solve a concrete real-world problem. Each one must name a
specific gap in the CURRENT schema/tables above — do not propose something
already fully supported.

Return ONLY a raw JSON array (no markdown fences, no commentary), each object
with exactly these keys: title, category, client_pain_point,
proposed_requirement, why_it_matters, related_gap, priority (High/Medium/Low),
effort (S/M/L)."""

    def parse_model_output(self, raw_text):
        match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        if not match:
            raise ValueError("no JSON array found in model output")
        items = json.loads(match.group(0))
        required = {"title", "category", "client_pain_point", "proposed_requirement",
                    "why_it_matters", "related_gap", "priority", "effort"}
        valid = [item for item in items if isinstance(item, dict) and required.issubset(item)]
        return valid

    def merge_and_formulate(self):
        existing_rows = self.load_existing()
        existing_titles = {r["title"].strip().lower() for r in existing_rows if r.get("title")}

        print("📋 Product Owner Agent: reading requirements.docx and current schema...")
        docx_text = self.extract_word_text()
        schema_summary = self.summarize_schema()

        print("🧠 Product Owner Agent: proposing new candidates via local llama3...")
        prompt = self.build_prompt(docx_text, schema_summary, existing_titles)

        try:
            response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
            raw_text = response["message"]["content"]
        except Exception as e:
            print(f"❌ Could not reach Ollama — CSV left unchanged. ({e})")
            return

        try:
            candidates = self.parse_model_output(raw_text)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"❌ Model output was not valid JSON — CSV left unchanged. ({e})")
            return

        next_id = self.next_id(existing_rows)
        today = date.today().isoformat()
        new_rows = []
        for item in candidates:
            if item["title"].strip().lower() in existing_titles:
                continue
            new_rows.append({
                "id": f"NR-{next_id:03d}",
                "status": "Proposed",
                "source": "llama3-agent",
                "date_added": today,
                **{k: item[k] for k in ("title", "category", "client_pain_point",
                                         "proposed_requirement", "why_it_matters",
                                         "related_gap", "priority", "effort")},
            })
            existing_titles.add(item["title"].strip().lower())
            next_id += 1

        if not new_rows:
            print("ℹ️ No new, non-duplicate candidates proposed this run — CSV left unchanged.")
            return

        with open(self.csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(existing_rows + new_rows)

        print(f"🎯 Added {len(new_rows)} new candidate(s) to {self.csv_path}")
        print("   Existing rows and their `status` were left untouched.")


if __name__ == "__main__":
    # Derived from this file's own location, not a hardcoded home path, so
    # it works from any checkout (see documentation_agent.py for why).
    agent = ProductOwnerAgent(os.path.dirname(os.path.abspath(__file__)))
    agent.merge_and_formulate()
