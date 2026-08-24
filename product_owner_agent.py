import os
import sys
from datetime import datetime
import ollama

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
        if not os.path.exists(self.docx_path):
            return "⚠️ Notice: 'requirements.docx' was not found in the root folder."
        try:
            doc = docx.Document(self.docx_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            return "\n".join(full_text)
        except Exception as e:
            return f"❌ Failed to parse Word document: {str(e)}"

    def merge_and_formulate(self):
        print("📋 [Free Local AI] Product Owner Agent: Analyzing Word document...")
        raw_word_text = self.extract_word_text()
        
        print("🧠 [Free Local AI] Product Owner Agent: Enhancing requirements locally using Llama 3...")
        
        prompt = f"""You are an elite enterprise Product Owner specializing in ServiceNow GRC.
Take the user's initial requirements from their Word document and ENHANCE them to resolve real-life risk problems.

Include:
1. Cascading Risks: Asset failures impacting up-stream components.
2. Control Self-Assessments: Automated validation criteria metrics.
3. Quantified Residual Risk Formula.

Here are the user's raw requirements:
{raw_word_text}

Compile a comprehensive markdown file titled '# 📋 Aligned Product Backlog'. Return ONLY raw markdown content. No chat filler."""

        try:
            # Call your free local model
            response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
            
            with open(self.backlog_path, "w") as f:
                f.write(response['message']['content'])
            print(f"🎯 Product Owner Agent complete! Saved to: {self.backlog_path}")
            
        except Exception as e:
            print(f"❌ Product Owner Agent failed to communicate with Ollama: {str(e)}")

if __name__ == "__main__":
    agent = ProductOwnerAgent(os.path.expanduser("~/Desktop/ai-agent-demo"))
    agent.merge_and_formulate()
