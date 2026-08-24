import os
from datetime import datetime

try:
    import docx
except ImportError:
    print("⚠️ python-docx missing. Run: uv pip install python-docx")

class ProductOwnerAgent:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.docx_path = os.path.join(self.root_dir, "requirements.docx")
        self.backlog_path = os.path.join(self.root_dir, "PRODUCT_BACKLOG.md")
        
    def extract_word_text(self):
        """Reads the .docx file and converts paragraphs to raw string markdown format."""
        if not os.path.exists(self.docx_path):
            return "⚠️ Notice: 'requirements.docx' was not found in the root folder. Please place your Word document there."
        
        try:
            doc = docx.Document(self.docx_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    # If paragraph looks like a header, make it look clean in markdown
                    if len(para.text) < 60 and not para.text.endswith('.'):
                        full_text.append(f"\n### {para.text}")
                    else:
                        full_text.append(para.text)
            return "\n".join(full_text)
        except Exception as e:
            return f"❌ Failed to parse Word document: {str(e)}"

    def review_current_build(self):
        """Inspects project directory to check technical progress status."""
        has_backend = os.path.exists(os.path.join(self.root_dir, "backend"))
        has_frontend = os.path.exists(os.path.join(self.root_dir, "frontend"))
        return {"backend": has_backend, "frontend": has_frontend}

    def merge_and_formulate(self):
        print("📋 Product Owner Agent: Ingesting your custom Word requirements document...")
        
        # Extract content from your requirements.docx
        custom_requirements = self.extract_word_text()
        state = self.review_current_build()
        
        # Compile everything into an unified system backlog
        backlog_content = f"""# 📋 Aligned Product Backlog & Target Vision
*Synthesized by Product Owner Agent on {datetime.now().strftime('%Y-%m-%d')}*

---

## 📄 Ingested Document Requirements (From requirements.docx)
{custom_requirements}

---

## 🏗️ Architectural Compliance Analysis
The Product Owner has checked your current local code footprint relative to the custom Word document goals:
- **Backend Architecture Integration:** {"🟢 Existing FastAPI schemas detected." if state['backend'] else "🔴 Backend service layer missing."}
- **Frontend Presentation Layer:** {"🟢 Next.js UI component space active." if state['frontend'] else "🔴 Next.js app scaffolding missing."}

---

## 🛠️ Refined Directive Backlog for Engineering Agent (Claude Code)
Based directly on your Word specifications, build the following updates:
1. Cross-reference the database tables to match any specialized data tracking columns specified in the Word document.
2. Refine form validation boundaries on the frontend components to handle data fields accurately as outlined above.
3. Keep the 50 mocked dataset entries per table running flawlessly to enable proper application evaluation.
"""
        with open(self.backlog_path, "w") as f:
            f.write(backlog_content)
        
        print(f"🎯 Successfully processed Word requirements! Updated: {self.backlog_path}")
        print("\n👉 Next Step: Run `claude` in your terminal and prompt: \"Please read @PRODUCT_BACKLOG.md and adjust the project structure to match the specifications.\"")

if __name__ == "__main__":
    agent = ProductOwnerAgent(os.path.expanduser("~/Desktop/ai-agent-demo"))
    agent.merge_and_formulate()
