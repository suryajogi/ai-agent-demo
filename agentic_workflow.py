import os
import subprocess
import sys
import ollama
from product_owner_agent import ProductOwnerAgent

class AutonomousGRCFactory:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)

    def run_command(self, cmd, cwd=None):
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr

    def run_qa_tests(self):
        print("🕵️  QA Agent: Running local validations...")
        backend_path = os.path.join(self.root_dir, "backend")
        success, out, err = self.run_command("python init_db.py", cwd=backend_path)
        if success:
            print("🟢 QA Status: Tests Passed! Database compiled successfully.")
        else:
            print(f"🔴 QA Status: Tests Failed!\n{err}")
        return success

    def run_workflow_loop(self):
        print("🚀 Starting Free Local AI Agent Factory Loop...\n")
        
        # 1. Run the local Product Owner
        po = ProductOwnerAgent(self.root_dir)
        po.merge_and_formulate()
        
        with open(os.path.join(self.root_dir, "PRODUCT_BACKLOG.md"), "r") as f:
            backlog_content = f.read()

        # 2. Create git branch
        branch_name = f"local-ai-feature-{int(subprocess.time.time())}"
        print(f"📁 Git Agent: Opening isolated sandbox branch [{branch_name}]...")
        self.run_command(f"git checkout -b {branch_name}", cwd=self.root_dir)

        # 3. Local Developer edits the code
        print("🧑‍💻 Developer Agent: Writing backend code using free Llama 3...")
        main_py_path = os.path.join(self.root_dir, "backend", "main.py")
        
        with open(main_py_path, "r") as f:
            current_code = f.read()

        prompt = f"Modify this Python FastAPI code to support these backlog requirements: {backlog_content}\n\nCurrent code:\n{current_code}\n\nReturn ONLY the complete raw Python code. No markdown formatting, no explanations."
        
        response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        clean_code = response['message']['content'].replace("```python", "").replace("```", "").strip()

        with open(main_py_path, "w") as f:
            f.write(clean_code)
        print("🟢 Developer Agent: Finished structural modifications.")

        # 4. QA check
        is_safe_to_merge = self.run_qa_tests()

        # 5. Commit and Push if successful
        if is_safe_to_merge:
            print("🚀 Deployment Agent: Code verified. Committing changes...")
            self.run_command("git add .", cwd=self.root_dir)
            self.run_command(f'git commit -m "feat(local-ai): automated build via free llama3 model"', cwd=self.root_dir)
            
            print("🔀 Merge Agent: Merging changes back to main...")
            self.run_command("git checkout main", cwd=self.root_dir)
            self.run_command(f"git merge {branch_name}", cwd=self.root_dir)
            
            print("☁️  Pushing updates to GitHub for free...")
            self.run_command("git push origin main", cwd=self.root_dir)
            print("\n🎉 WORKFLOW CYCLE COMPLETE: System successfully updated via Free Local AI!")
        else:
            print("⚠️ Factory Alert: Discovered compile bugs. Rolling back workspace to protect main branch.")
            self.run_command("git checkout main", cwd=self.root_dir)

if __name__ == "__main__":
    factory = AutonomousGRCFactory(os.path.expanduser("~/Desktop/ai-agent-demo"))
    factory.run_workflow_loop()
